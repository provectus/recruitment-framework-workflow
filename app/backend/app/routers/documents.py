from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.dependencies.auth import get_current_user
from app.exceptions import ConflictError, ForbiddenError, NotFoundException
from app.models.user import User
from app.schemas.documents import (
    DocumentDetailResponse,
    DocumentResponse,
    PasteTranscriptRequest,
    PresignRequest,
    PresignResponse,
)
from app.services import document_service

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post(
    "/presign", response_model=PresignResponse, status_code=status.HTTP_201_CREATED
)
async def presign_upload(
    body: PresignRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> PresignResponse:
    if current_user.id is None:
        raise HTTPException(status_code=401, detail="User ID missing")
    try:
        document, upload_url = await document_service.create_presigned_upload(
            session=session,
            type=body.type,
            candidate_position_id=body.candidate_position_id,
            file_name=body.file_name,
            content_type=body.content_type,
            file_size=body.file_size,
            uploaded_by_id=current_user.id,
            interview_stage=body.interview_stage,
            interviewer_id=body.interviewer_id,
            interview_date=body.interview_date,
            notes=body.notes,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.detail) from e

    return PresignResponse(
        document_id=document.id,
        upload_url=upload_url,
        s3_key=document.s3_key,
    )


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> DocumentDetailResponse:
    if current_user.id is None:
        raise HTTPException(status_code=401, detail="User ID missing")
    try:
        document = await document_service.get_document(
            session=session,
            document_id=document_id,
            user_id=current_user.id,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.detail) from e
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=e.detail) from e
    return DocumentDetailResponse(**document)


@router.post("/{document_id}/complete", response_model=DocumentResponse)
async def complete_upload(
    document_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> DocumentResponse:
    if current_user.id is None:
        raise HTTPException(status_code=401, detail="User ID missing")
    try:
        document = await document_service.complete_upload(
            session=session,
            document_id=document_id,
            user_id=current_user.id,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.detail) from e
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=e.detail) from e
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=e.detail) from e

    enriched = await document_service.enrich_document_response(session, document)
    return DocumentResponse(**enriched)


@router.post(
    "/paste", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED
)
async def paste_transcript(
    body: PasteTranscriptRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> DocumentResponse:
    if current_user.id is None:
        raise HTTPException(status_code=401, detail="User ID missing")
    try:
        document = await document_service.create_pasted_transcript(
            session=session,
            candidate_position_id=body.candidate_position_id,
            content=body.content,
            interview_stage=body.interview_stage,
            interviewer_id=body.interviewer_id,
            interview_date=body.interview_date,
            uploaded_by_id=current_user.id,
            notes=body.notes,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.detail) from e

    enriched = await document_service.enrich_document_response(session, document)
    return DocumentResponse(**enriched)
