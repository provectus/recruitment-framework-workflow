import logging

from sqlalchemy import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.exceptions import NotFoundException
from app.models.candidate_position import CandidatePosition
from app.models.enums import EvaluationStatus, EvaluationStepType
from app.models.evaluation import Evaluation
from app.services import eventbridge_service

logger = logging.getLogger(__name__)


async def get_evaluations(
    session: AsyncSession,
    candidate_position_id: int,
) -> list[Evaluation]:
    max_version_subq = (
        select(
            Evaluation.step_type,
            func.max(Evaluation.version).label("max_version"),
        )
        .where(Evaluation.candidate_position_id == candidate_position_id)
        .group_by(Evaluation.step_type)
        .subquery()
    )

    query = (
        select(Evaluation)
        .join(
            max_version_subq,
            (Evaluation.step_type == max_version_subq.c.step_type)
            & (Evaluation.version == max_version_subq.c.max_version),
        )
        .where(Evaluation.candidate_position_id == candidate_position_id)
        .order_by(Evaluation.step_type)
    )

    result = await session.execute(query)
    return list(result.scalars().all())


async def get_evaluation_by_step(
    session: AsyncSession,
    candidate_position_id: int,
    step_type: str,
) -> Evaluation:
    query = (
        select(Evaluation)
        .where(Evaluation.candidate_position_id == candidate_position_id)
        .where(Evaluation.step_type == step_type)
        .order_by(Evaluation.version.desc())
        .limit(1)
    )

    result = await session.execute(query)
    evaluation = result.scalar_one_or_none()

    if evaluation is None:
        raise NotFoundException(
            f"No evaluation found for step '{step_type}' "
            f"on candidate position {candidate_position_id}"
        )

    return evaluation


async def get_evaluation_history(
    session: AsyncSession,
    candidate_position_id: int,
    step_type: str,
) -> list[Evaluation]:
    query = (
        select(Evaluation)
        .where(Evaluation.candidate_position_id == candidate_position_id)
        .where(Evaluation.step_type == step_type)
        .order_by(Evaluation.version.desc())
    )

    result = await session.execute(query)
    return list(result.scalars().all())


async def create_evaluation(
    session: AsyncSession,
    candidate_position_id: int,
    step_type: str,
    source_document_id: int | None = None,
    rubric_version_id: int | None = None,
    _max_retries: int = 3,
) -> Evaluation:
    from sqlalchemy.exc import IntegrityError

    candidate_position = await session.get(CandidatePosition, candidate_position_id)
    if candidate_position is None:
        raise NotFoundException(f"Candidate position {candidate_position_id} not found")

    for attempt in range(_max_retries):
        latest_version_query = (
            select(Evaluation.version)
            .where(Evaluation.candidate_position_id == candidate_position_id)
            .where(Evaluation.step_type == step_type)
            .order_by(Evaluation.version.desc())
            .limit(1)
        )
        result = await session.execute(latest_version_query)
        latest_version = result.scalar_one_or_none()
        next_version = (latest_version or 0) + 1

        evaluation = Evaluation(
            candidate_position_id=candidate_position_id,
            step_type=EvaluationStepType(step_type),
            status=EvaluationStatus.pending,
            version=next_version,
            source_document_id=source_document_id,
            rubric_version_id=rubric_version_id,
        )

        session.add(evaluation)
        try:
            await session.commit()
            await session.refresh(evaluation)
            return evaluation
        except IntegrityError:
            await session.rollback()
            if attempt == _max_retries - 1:
                raise

    raise RuntimeError("Unreachable: retry loop exited without return or raise")


async def trigger_evaluation(
    session: AsyncSession,
    candidate_position_id: int,
    step_type: str,
    source_document_id: int | None = None,
    rubric_version_id: int | None = None,
) -> Evaluation:
    evaluation = await create_evaluation(
        session=session,
        candidate_position_id=candidate_position_id,
        step_type=step_type,
        source_document_id=source_document_id,
        rubric_version_id=rubric_version_id,
    )

    try:
        await eventbridge_service.publish_evaluation_event(
            evaluation_id=evaluation.id,
            candidate_position_id=candidate_position_id,
            step_type=step_type,
            source_document_id=source_document_id,
            rubric_version_id=rubric_version_id,
        )
    except Exception:
        evaluation.status = EvaluationStatus.failed
        evaluation.error_message = "Failed to publish evaluation event"
        session.add(evaluation)
        await session.commit()
        await session.refresh(evaluation)
        logger.error(
            "Failed to publish event for evaluation_id=%s step_type=%s — marked failed",
            evaluation.id,
            step_type,
            exc_info=True,
        )

    return evaluation


async def trigger_feedback_gen(
    session: AsyncSession,
    candidate_position_id: int,
) -> Evaluation:
    existing = await _latest_evaluation_for_step(
        session, candidate_position_id, EvaluationStepType.feedback_gen
    )
    if existing and existing.status in (
        EvaluationStatus.pending,
        EvaluationStatus.running,
    ):
        logger.info(
            "Skipping duplicate feedback_gen trigger — evaluation_id=%s is already %s",
            existing.id,
            existing.status,
        )
        return existing

    return await trigger_evaluation(
        session=session,
        candidate_position_id=candidate_position_id,
        step_type=EvaluationStepType.feedback_gen,
    )


async def verify_access(
    session: AsyncSession,
    candidate_position_id: int,
    user_id: int,
) -> None:
    from app.models.document import Document
    from app.models.position import Position

    cp = await session.get(CandidatePosition, candidate_position_id)
    if cp is None:
        raise NotFoundException(f"Candidate position {candidate_position_id} not found")

    position = await session.get(Position, cp.position_id)
    if position is not None and position.hiring_manager_id == user_id:
        return

    doc_query = (
        select(Document.id)
        .where(Document.candidate_position_id == candidate_position_id)
        .where(Document.uploaded_by_id == user_id)
        .limit(1)
    )
    result = await session.execute(doc_query)
    if result.scalar_one_or_none() is not None:
        return

    raise NotFoundException(f"Candidate position {candidate_position_id} not found")


async def _latest_evaluation_for_step(
    session: AsyncSession,
    candidate_position_id: int,
    step_type: EvaluationStepType,
) -> Evaluation | None:
    query = (
        select(Evaluation)
        .where(Evaluation.candidate_position_id == candidate_position_id)
        .where(Evaluation.step_type == step_type)
        .order_by(Evaluation.version.desc())
        .limit(1)
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def rerun_evaluation(
    session: AsyncSession,
    candidate_position_id: int,
    step_type: str,
) -> list[Evaluation]:
    step = EvaluationStepType(step_type)

    latest = await _latest_evaluation_for_step(session, candidate_position_id, step)
    if latest is None:
        raise NotFoundException(
            f"No evaluation found for step '{step_type}' "
            f"on candidate position {candidate_position_id}"
        )

    rerun = await trigger_evaluation(
        session=session,
        candidate_position_id=candidate_position_id,
        step_type=step_type,
        source_document_id=latest.source_document_id,
        rubric_version_id=latest.rubric_version_id,
    )

    return [rerun]
