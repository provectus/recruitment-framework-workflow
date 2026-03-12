import asyncio
import json
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel.ext.asyncio.session import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.database import async_session_factory, get_session
from app.dependencies.auth import get_current_user
from app.exceptions import NotFoundException
from app.models.enums import EvaluationStatus, EvaluationStepType
from app.models.user import User
from app.schemas.evaluations import (
    EvaluationHistoryResponse,
    EvaluationListResponse,
    EvaluationResponse,
)
from app.services import evaluation_service

router = APIRouter(prefix="/api/evaluations", tags=["evaluations"])


def _require_user_id(user: User) -> int:
    if user.id is None:
        raise HTTPException(status_code=401, detail="User ID not available")
    return user.id


TERMINAL_STATUSES = {EvaluationStatus.completed, EvaluationStatus.failed}
POLL_INTERVAL_SECONDS = 2
KEEPALIVE_INTERVAL_POLLS = 15
MAX_POLL_DURATION_SECONDS = 300

VALID_STEP_TYPES = {member.value for member in EvaluationStepType}


def _validate_step_type(step_type: str) -> None:
    if step_type not in VALID_STEP_TYPES:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Invalid step_type '{step_type}'. "
                f"Must be one of: {sorted(VALID_STEP_TYPES)}"
            ),
        )


@router.get("/{candidate_position_id}/stream")
async def stream_evaluation_status(
    candidate_position_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> EventSourceResponse:
    async def event_generator() -> AsyncGenerator[dict[str, str], None]:
        last_known_statuses: dict[str, str] = {}
        keepalive_counter = 0
        access_verified = False
        started_at = asyncio.get_running_loop().time()

        while True:
            elapsed = asyncio.get_running_loop().time() - started_at
            if elapsed >= MAX_POLL_DURATION_SECONDS:
                yield {"event": "done", "data": "{}"}
                break

            if await request.is_disconnected():
                break

            async with async_session_factory() as poll_session:
                if not access_verified:
                    user_id = _require_user_id(current_user)
                    await evaluation_service.verify_access(
                        poll_session, candidate_position_id, user_id
                    )
                    access_verified = True
                evaluations = await evaluation_service.get_evaluations(
                    poll_session, candidate_position_id
                )

            for evaluation in evaluations:
                eval_key = str(evaluation.id)
                current_status = evaluation.status

                if (
                    eval_key not in last_known_statuses
                    or last_known_statuses[eval_key] != current_status
                ):
                    last_known_statuses[eval_key] = current_status
                    yield {
                        "event": "status_change",
                        "data": json.dumps(
                            {
                                "evaluation_id": evaluation.id,
                                "step_type": evaluation.step_type,
                                "status": current_status,
                            }
                        ),
                    }

            if evaluations and all(e.status in TERMINAL_STATUSES for e in evaluations):
                yield {"event": "done", "data": "{}"}
                break

            if not evaluations and last_known_statuses:
                yield {"event": "done", "data": "{}"}
                break

            keepalive_counter += 1
            if keepalive_counter >= KEEPALIVE_INTERVAL_POLLS:
                keepalive_counter = 0
                yield {"comment": "keepalive"}

            await asyncio.sleep(POLL_INTERVAL_SECONDS)

    return EventSourceResponse(event_generator())


@router.get("/{candidate_position_id}", response_model=EvaluationListResponse)
async def list_evaluations(
    candidate_position_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> EvaluationListResponse:
    user_id = _require_user_id(current_user)
    try:
        await evaluation_service.verify_access(session, candidate_position_id, user_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.detail) from e
    evaluations = await evaluation_service.get_evaluations(
        session=session,
        candidate_position_id=candidate_position_id,
    )
    return EvaluationListResponse(
        items=[EvaluationResponse.model_validate(e) for e in evaluations]
    )


@router.post(
    "/{candidate_position_id}/{step_type}/rerun",
    response_model=EvaluationListResponse,
)
async def rerun_evaluation(
    candidate_position_id: int,
    step_type: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> EvaluationListResponse:
    _validate_step_type(step_type)
    user_id = _require_user_id(current_user)
    try:
        await evaluation_service.verify_access(session, candidate_position_id, user_id)
        evaluations = await evaluation_service.rerun_evaluation(
            session=session,
            candidate_position_id=candidate_position_id,
            step_type=step_type,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.detail) from e
    return EvaluationListResponse(
        items=[EvaluationResponse.model_validate(e) for e in evaluations]
    )


@router.get(
    "/{candidate_position_id}/{step_type}/history",
    response_model=EvaluationHistoryResponse,
)
async def get_evaluation_history(
    candidate_position_id: int,
    step_type: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> EvaluationHistoryResponse:
    _validate_step_type(step_type)
    user_id = _require_user_id(current_user)
    try:
        await evaluation_service.verify_access(session, candidate_position_id, user_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.detail) from e
    evaluations = await evaluation_service.get_evaluation_history(
        session=session,
        candidate_position_id=candidate_position_id,
        step_type=step_type,
    )
    return EvaluationHistoryResponse(
        step_type=step_type,
        items=[EvaluationResponse.model_validate(e) for e in evaluations],
    )


@router.get(
    "/{candidate_position_id}/{step_type}",
    response_model=EvaluationResponse,
)
async def get_evaluation_by_step(
    candidate_position_id: int,
    step_type: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> EvaluationResponse:
    _validate_step_type(step_type)
    user_id = _require_user_id(current_user)
    try:
        await evaluation_service.verify_access(session, candidate_position_id, user_id)
        evaluation = await evaluation_service.get_evaluation_by_step(
            session=session,
            candidate_position_id=candidate_position_id,
            step_type=step_type,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.detail) from e
    return EvaluationResponse.model_validate(evaluation)
