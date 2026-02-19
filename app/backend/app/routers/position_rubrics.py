from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.dependencies.auth import get_current_user
from app.exceptions import ConflictError, NotFoundException, ValidationError
from app.models.user import User
from app.schemas.position_rubrics import (
    PositionRubricCreate,
    PositionRubricResponse,
    PositionRubricUpdate,
    PositionRubricVersionListResponse,
    SaveAsTemplateRequest,
)
from app.schemas.rubric_templates import RubricTemplateDetail
from app.services import position_rubric_service

router = APIRouter(prefix="/api/positions", tags=["position-rubrics"])


@router.post(
    "/{position_id}/rubric",
    response_model=PositionRubricResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_position_rubric(
    position_id: int,
    body: PositionRubricCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> PositionRubricResponse:
    assert current_user.id is not None
    try:
        result = await position_rubric_service.create_rubric(
            session,
            position_id=position_id,
            source=body.source,
            template_id=body.template_id,
            structure_dict=body.structure.model_dump()
            if body.structure is not None
            else None,
            user_id=current_user.id,
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.detail,
        ) from e
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail,
        ) from e
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.detail,
        ) from e
    return PositionRubricResponse(**result)


@router.get(
    "/{position_id}/rubric",
    response_model=PositionRubricResponse,
)
async def get_position_rubric(
    position_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> PositionRubricResponse:
    try:
        result = await position_rubric_service.get_active_rubric(session, position_id)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail,
        ) from e
    return PositionRubricResponse(**result)


@router.put("/{position_id}/rubric", response_model=PositionRubricResponse)
async def update_position_rubric(
    position_id: int,
    body: PositionRubricUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> PositionRubricResponse:
    assert current_user.id is not None
    try:
        result = await position_rubric_service.update_rubric(
            session,
            position_id=position_id,
            structure_dict=body.structure.model_dump(),
            user_id=current_user.id,
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail,
        ) from e
    return PositionRubricResponse(**result)


@router.delete("/{position_id}/rubric", status_code=status.HTTP_204_NO_CONTENT)
async def delete_position_rubric(
    position_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        await position_rubric_service.delete_rubric(session, position_id)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail,
        ) from e


@router.get(
    "/{position_id}/rubric/versions",
    response_model=PositionRubricVersionListResponse,
)
async def list_rubric_versions(
    position_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> PositionRubricVersionListResponse:
    try:
        items = await position_rubric_service.list_versions(session, position_id)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail,
        ) from e
    return PositionRubricVersionListResponse(items=items)


@router.get(
    "/{position_id}/rubric/versions/{version_number}",
    response_model=PositionRubricResponse,
)
async def get_rubric_version(
    position_id: int,
    version_number: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> PositionRubricResponse:
    try:
        result = await position_rubric_service.get_version(
            session, position_id, version_number
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail,
        ) from e
    return PositionRubricResponse(**result)


@router.post(
    "/{position_id}/rubric/revert/{version_number}",
    response_model=PositionRubricResponse,
)
async def revert_rubric_version(
    position_id: int,
    version_number: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> PositionRubricResponse:
    assert current_user.id is not None
    try:
        result = await position_rubric_service.revert_to_version(
            session, position_id, version_number, current_user.id
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail,
        ) from e
    return PositionRubricResponse(**result)


@router.post(
    "/{position_id}/rubric/save-as-template",
    response_model=RubricTemplateDetail,
    status_code=status.HTTP_201_CREATED,
)
async def save_rubric_as_template(
    position_id: int,
    body: SaveAsTemplateRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> RubricTemplateDetail:
    try:
        result = await position_rubric_service.save_as_template(
            session,
            position_id=position_id,
            name=body.name,
            description=body.description,
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail,
        ) from e
    return RubricTemplateDetail(**result)
