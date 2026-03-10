import logging
import re
from datetime import date
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import aliased
from sqlmodel.ext.asyncio.session import AsyncSession

from app.exceptions import ConflictError, ForbiddenError, NotFoundException
from app.models.candidate_position import CandidatePosition
from app.models.document import Document
from app.models.enums import DocumentStatus, DocumentType, InputMethod, InterviewStage
from app.models.position import Position
from app.models.position_rubric import PositionRubric, PositionRubricVersion
from app.models.user import User
from app.services import evaluation_service, storage_service

logger = logging.getLogger(__name__)

MAX_FILE_NAME_LENGTH = 255
_UNSAFE_CHARS = re.compile(r"[/\\:\x00-\x1f\x7f]")


async def _get_latest_rubric_version_id(
    session: AsyncSession, position_id: int
) -> int | None:
    rubric_stmt = select(PositionRubric).where(
        PositionRubric.position_id == position_id
    )
    rubric_result = await session.exec(rubric_stmt)
    rubric = rubric_result.first()
    if rubric is None:
        return None

    version_stmt = (
        select(PositionRubricVersion)
        .where(PositionRubricVersion.position_rubric_id == rubric.id)
        .order_by(PositionRubricVersion.version_number.desc())
        .limit(1)
    )
    version_result = await session.exec(version_stmt)
    version = version_result.first()
    return version.id if version is not None else None


async def _maybe_trigger_evaluation(session: AsyncSession, document: Document) -> None:
    doc_type = document.type
    interview_stage = document.interview_stage

    if doc_type == DocumentType.cv:
        step_type = "cv_analysis"
        rubric_version_id = None
    elif (
        doc_type == DocumentType.transcript
        and interview_stage == InterviewStage.screening
    ):
        step_type = "screening_eval"
        rubric_version_id = None
    elif (
        doc_type == DocumentType.transcript
        and interview_stage == InterviewStage.technical
    ):
        candidate_position = await session.get(
            CandidatePosition, document.candidate_position_id
        )
        if candidate_position is None:
            logger.warning(
                "Skipping evaluation trigger: candidate_position %s not found",
                document.candidate_position_id,
            )
            return

        rubric_version_id = await _get_latest_rubric_version_id(
            session, candidate_position.position_id
        )
        if rubric_version_id is None:
            logger.info(
                "Skipping technical_eval trigger: no rubric assigned to position %s",
                candidate_position.position_id,
            )
            return

        step_type = "technical_eval"
    else:
        return

    try:
        await evaluation_service.trigger_evaluation(
            session=session,
            candidate_position_id=document.candidate_position_id,
            step_type=step_type,
            source_document_id=document.id,
            rubric_version_id=rubric_version_id,
        )
    except Exception:
        logger.warning(
            "Failed to trigger evaluation for document %s step_type=%s",
            document.id,
            step_type,
            exc_info=True,
        )


async def _user_can_access_candidate_documents(
    session: AsyncSession,
    candidate_id: int,
    user_id: int,
) -> bool:
    uploaded_query = (
        select(Document.id)
        .join(CandidatePosition, Document.candidate_position_id == CandidatePosition.id)
        .where(CandidatePosition.candidate_id == candidate_id)
        .where(Document.uploaded_by_id == user_id)
        .limit(1)
    )
    uploaded_result = await session.exec(uploaded_query)
    if uploaded_result.first() is not None:
        return True

    hiring_manager_query = (
        select(Position.id)
        .join(CandidatePosition, CandidatePosition.position_id == Position.id)
        .where(CandidatePosition.candidate_id == candidate_id)
        .where(Position.hiring_manager_id == user_id)
        .limit(1)
    )
    hm_result = await session.exec(hiring_manager_query)
    return hm_result.first() is not None


def _sanitize_file_name(file_name: str) -> str:
    sanitized = _UNSAFE_CHARS.sub("_", file_name).strip(". ")
    if len(sanitized) > MAX_FILE_NAME_LENGTH:
        sanitized = sanitized[:MAX_FILE_NAME_LENGTH]
    if not sanitized:
        sanitized = "unnamed"
    return sanitized


async def create_presigned_upload(
    session: AsyncSession,
    type: str,
    candidate_position_id: int,
    file_name: str,
    content_type: str,
    file_size: int,
    uploaded_by_id: int,
    interview_stage: str | None = None,
    interviewer_id: int | None = None,
    interview_date: date | None = None,
    notes: str | None = None,
) -> tuple[Document, str]:
    candidate_position = await session.get(CandidatePosition, candidate_position_id)
    if candidate_position is None:
        raise NotFoundException(f"Candidate position {candidate_position_id} not found")

    if interviewer_id is not None:
        interviewer = await session.get(User, interviewer_id)
        if interviewer is None:
            raise NotFoundException(f"Interviewer (user {interviewer_id}) not found")

    safe_name = _sanitize_file_name(file_name)
    s3_key = f"documents/{uuid4()}/{safe_name}"

    document = Document(
        type=type,
        candidate_position_id=candidate_position_id,
        file_name=file_name,
        s3_key=s3_key,
        file_size=file_size,
        content_type=content_type,
        status=DocumentStatus.pending,
        interview_stage=interview_stage,
        interviewer_id=interviewer_id,
        interview_date=interview_date,
        notes=notes,
        input_method=InputMethod.file,
        uploaded_by_id=uploaded_by_id,
    )

    session.add(document)
    await session.flush()

    upload_url = await storage_service.generate_upload_url(
        s3_key=s3_key,
        content_type=content_type,
        max_size=file_size,
    )

    await session.commit()

    return document, upload_url


async def complete_upload(
    session: AsyncSession,
    document_id: int,
    user_id: int,
) -> Document:
    document = await session.get(Document, document_id)
    if document is None:
        raise NotFoundException(f"Document {document_id} not found")

    if document.uploaded_by_id != user_id:
        raise ForbiddenError("Document not owned by current user")

    if document.status != DocumentStatus.pending:
        raise ConflictError(f"Document already completed (status: {document.status})")

    if document.file_size is not None:
        actual_size = await storage_service.get_object_size(document.s3_key)
        max_allowed = int(document.file_size * 1.05)
        if actual_size > max_allowed:
            await storage_service.delete_object(document.s3_key)
            raise ConflictError(
                f"Uploaded file size ({actual_size} bytes) exceeds "
                f"declared size ({document.file_size} bytes)"
            )

    document.status = DocumentStatus.active

    session.add(document)
    await session.commit()
    await session.refresh(document)

    await _maybe_trigger_evaluation(session, document)

    return document


async def create_pasted_transcript(
    session: AsyncSession,
    candidate_position_id: int,
    content: str,
    interview_stage: str,
    interviewer_id: int,
    interview_date: date,
    uploaded_by_id: int,
    notes: str | None = None,
) -> Document:
    candidate_position = await session.get(CandidatePosition, candidate_position_id)
    if candidate_position is None:
        raise NotFoundException(f"Candidate position {candidate_position_id} not found")

    interviewer = await session.get(User, interviewer_id)
    if interviewer is None:
        raise NotFoundException(f"Interviewer (user {interviewer_id}) not found")

    s3_key = f"documents/{uuid4()}/transcript.txt"

    document = Document(
        type=DocumentType.transcript,
        candidate_position_id=candidate_position_id,
        file_name=None,
        s3_key=s3_key,
        file_size=None,
        content_type="text/plain",
        status=DocumentStatus.active,
        interview_stage=interview_stage,
        interviewer_id=interviewer_id,
        interview_date=interview_date,
        notes=notes,
        input_method=InputMethod.paste,
        uploaded_by_id=uploaded_by_id,
    )

    session.add(document)
    await session.flush()

    await storage_service.put_text_object(s3_key, content, "text/plain")

    await session.commit()
    await session.refresh(document)

    await _maybe_trigger_evaluation(session, document)

    return document


async def enrich_document_response(
    session: AsyncSession,
    document: Document,
) -> dict:
    interviewer_name = None
    if document.interviewer_id is not None:
        interviewer = await session.get(User, document.interviewer_id)
        if interviewer is not None:
            interviewer_name = interviewer.full_name

    uploaded_by = await session.get(User, document.uploaded_by_id)
    uploaded_by_name = uploaded_by.full_name if uploaded_by is not None else None

    return {
        "id": document.id,
        "type": document.type,
        "candidate_position_id": document.candidate_position_id,
        "file_name": document.file_name,
        "file_size": document.file_size,
        "content_type": document.content_type,
        "status": document.status,
        "interview_stage": document.interview_stage,
        "interviewer_id": document.interviewer_id,
        "interviewer_name": interviewer_name,
        "interview_date": document.interview_date,
        "notes": document.notes,
        "input_method": document.input_method,
        "uploaded_by_id": document.uploaded_by_id,
        "uploaded_by_name": uploaded_by_name,
        "created_at": document.created_at,
        "updated_at": document.updated_at,
    }


async def get_document(
    session: AsyncSession,
    document_id: int,
    user_id: int,
) -> dict:
    document = await session.get(Document, document_id)
    if document is None:
        raise NotFoundException(f"Document {document_id} not found")

    candidate_position = await session.get(
        CandidatePosition, document.candidate_position_id
    )
    if candidate_position is None:
        raise NotFoundException(
            f"Document {document_id} references missing candidate position"
        )
    if not await _user_can_access_candidate_documents(
        session, candidate_position.candidate_id, user_id
    ):
        raise ForbiddenError("Not authorized to view this document")

    result = await enrich_document_response(session, document)

    view_url = await storage_service.generate_view_url(
        s3_key=document.s3_key,
        expiration=3600,
    )
    result["view_url"] = view_url

    return result


async def list_candidate_documents(
    session: AsyncSession,
    candidate_id: int,
    user_id: int,
    position_id: int | None = None,
    type: str | None = None,
    candidate_position_id: int | None = None,
) -> list[dict]:
    if not await _user_can_access_candidate_documents(session, candidate_id, user_id):
        raise ForbiddenError("Not authorized to view documents for this candidate")

    InterviewerUser = aliased(User)
    UploadedByUser = aliased(User)

    query = (
        select(Document, InterviewerUser, UploadedByUser)
        .join(CandidatePosition, Document.candidate_position_id == CandidatePosition.id)
        .outerjoin(InterviewerUser, Document.interviewer_id == InterviewerUser.id)
        .outerjoin(UploadedByUser, Document.uploaded_by_id == UploadedByUser.id)
        .where(CandidatePosition.candidate_id == candidate_id)
        .where(Document.status == DocumentStatus.active)
    )

    if position_id is not None:
        query = query.where(CandidatePosition.position_id == position_id)

    if candidate_position_id is not None:
        query = query.where(Document.candidate_position_id == candidate_position_id)

    if type is not None:
        query = query.where(Document.type == type)

    query = query.order_by(Document.created_at.desc())

    result = await session.execute(query)
    rows = result.all()

    documents = []
    for document, interviewer, uploaded_by in rows:
        interviewer_name = interviewer.full_name if interviewer is not None else None
        uploaded_by_name = uploaded_by.full_name if uploaded_by is not None else None

        documents.append(
            {
                "id": document.id,
                "type": document.type,
                "candidate_position_id": document.candidate_position_id,
                "file_name": document.file_name,
                "file_size": document.file_size,
                "content_type": document.content_type,
                "status": document.status,
                "interview_stage": document.interview_stage,
                "interviewer_id": document.interviewer_id,
                "interviewer_name": interviewer_name,
                "interview_date": document.interview_date,
                "notes": document.notes,
                "input_method": document.input_method,
                "uploaded_by_id": document.uploaded_by_id,
                "uploaded_by_name": uploaded_by_name,
                "created_at": document.created_at,
                "updated_at": document.updated_at,
            }
        )

    return documents
