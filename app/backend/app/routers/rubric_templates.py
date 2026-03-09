from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.dependencies.auth import get_current_user
from app.exceptions import NotFoundException
from app.models.user import User
from app.schemas.rubric_templates import (
    RubricTemplateArchiveResponse,
    RubricTemplateCreate,
    RubricTemplateDetail,
    RubricTemplateListItem,
    RubricTemplateListResponse,
    RubricTemplateUpdate,
)
from app.services import rubric_template_service

router = APIRouter(prefix="/api/rubric-templates", tags=["rubric-templates"])


@router.get("", response_model=RubricTemplateListResponse)
async def list_rubric_templates(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> RubricTemplateListResponse:
    templates = await rubric_template_service.list_templates(session)
    template_ids = [t.id for t in templates if t.id is not None]
    position_counts = await rubric_template_service.count_positions_by_templates(
        session, template_ids
    )
    items = [
        RubricTemplateListItem(
            id=template.id,
            name=template.name,
            description=template.description,
            category_count=len(template.structure.get("categories", [])),
            position_count=position_counts.get(template.id, 0),
            created_at=template.created_at,
        )
        for template in templates
        if template.id is not None
    ]
    return RubricTemplateListResponse(items=items, total=len(items))


@router.post(
    "",
    response_model=RubricTemplateDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_rubric_template(
    body: RubricTemplateCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> RubricTemplateDetail:
    template = await rubric_template_service.create_template(
        session,
        name=body.name,
        description=body.description,
        structure=body.structure.model_dump(),
    )
    return RubricTemplateDetail(
        id=template.id,
        name=template.name,
        description=template.description,
        structure=template.structure,
        is_archived=template.is_archived,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.get("/{template_id}", response_model=RubricTemplateDetail)
async def get_rubric_template(
    template_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> RubricTemplateDetail:
    try:
        template = await rubric_template_service.get_template(session, template_id)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=e.detail
        ) from e
    return RubricTemplateDetail(
        id=template.id,
        name=template.name,
        description=template.description,
        structure=template.structure,
        is_archived=template.is_archived,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.patch("/{template_id}", response_model=RubricTemplateDetail)
async def update_rubric_template(
    template_id: int,
    body: RubricTemplateUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> RubricTemplateDetail:
    try:
        template = await rubric_template_service.update_template(
            session,
            template_id,
            name=body.name,
            description=body.description,
            structure=body.structure.model_dump()
            if body.structure is not None
            else None,
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=e.detail
        ) from e
    return RubricTemplateDetail(
        id=template.id,
        name=template.name,
        description=template.description,
        structure=template.structure,
        is_archived=template.is_archived,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.post(
    "/{template_id}/duplicate",
    response_model=RubricTemplateDetail,
    status_code=status.HTTP_201_CREATED,
)
async def duplicate_rubric_template(
    template_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> RubricTemplateDetail:
    try:
        template = await rubric_template_service.duplicate_template(
            session, template_id
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=e.detail
        ) from e
    return RubricTemplateDetail(
        id=template.id,
        name=template.name,
        description=template.description,
        structure=template.structure,
        is_archived=template.is_archived,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.post("/{template_id}/archive", response_model=RubricTemplateArchiveResponse)
async def archive_rubric_template(
    template_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> RubricTemplateArchiveResponse:
    try:
        template, position_count = await rubric_template_service.archive_template(
            session, template_id
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=e.detail
        ) from e
    return RubricTemplateArchiveResponse(
        id=template.id,
        is_archived=template.is_archived,
        position_count=position_count,
    )
