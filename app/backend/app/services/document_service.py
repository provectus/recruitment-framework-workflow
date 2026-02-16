from datetime import date
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import aliased
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.candidate_position import CandidatePosition
from app.models.document import Document
from app.models.enums import DocumentStatus, DocumentType, InputMethod
from app.models.position import Position
from app.models.user import User
from app.services import storage_service


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
        raise HTTPException(
            status_code=404,
            detail=f"Candidate position {candidate_position_id} not found",
        )

    if interviewer_id is not None:
        interviewer = await session.get(User, interviewer_id)
        if interviewer is None:
            raise HTTPException(
                status_code=404,
                detail=f"Interviewer (user {interviewer_id}) not found",
            )

    s3_key = f"documents/{uuid4()}/{file_name}"

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
    await session.commit()

    upload_url = await storage_service.generate_upload_url(
        s3_key=s3_key,
        content_type=content_type,
        max_size=file_size,
    )

    return document, upload_url


async def complete_upload(
    session: AsyncSession,
    document_id: int,
    user_id: int,
) -> Document:
    document = await session.get(Document, document_id)
    if document is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document {document_id} not found",
        )

    if document.uploaded_by_id != user_id:
        raise HTTPException(
            status_code=409,
            detail="Document not owned by current user",
        )

    if document.status != DocumentStatus.pending:
        raise HTTPException(
            status_code=409,
            detail=f"Document already completed (status: {document.status})",
        )

    if document.file_size is not None:
        actual_size = await storage_service.get_object_size(document.s3_key)
        max_allowed = int(document.file_size * 1.05)
        if actual_size > max_allowed:
            await storage_service.delete_object(document.s3_key)
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Uploaded file size ({actual_size} bytes) exceeds "
                    f"declared size ({document.file_size} bytes)"
                ),
            )

    document.status = DocumentStatus.active

    session.add(document)
    await session.commit()
    await session.refresh(document)

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
        raise HTTPException(
            status_code=404,
            detail=f"Candidate position {candidate_position_id} not found",
        )

    interviewer = await session.get(User, interviewer_id)
    if interviewer is None:
        raise HTTPException(
            status_code=404,
            detail=f"Interviewer (user {interviewer_id}) not found",
        )

    s3_key = f"documents/{uuid4()}/transcript.txt"

    await storage_service.put_text_object(s3_key, content, "text/plain")

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
    await session.commit()

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
        raise HTTPException(
            status_code=404,
            detail=f"Document {document_id} not found",
        )

    candidate_position = await session.get(
        CandidatePosition, document.candidate_position_id
    )
    if not await _user_can_access_candidate_documents(
        session, candidate_position.candidate_id, user_id
    ):
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view this document",
        )

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
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view documents for this candidate",
        )

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
