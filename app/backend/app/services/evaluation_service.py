from sqlalchemy import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.exceptions import NotFoundException
from app.models.candidate_position import CandidatePosition
from app.models.enums import EvaluationStatus, EvaluationStepType
from app.models.evaluation import Evaluation
from app.services import eventbridge_service


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
) -> Evaluation:
    candidate_position = await session.get(CandidatePosition, candidate_position_id)
    if candidate_position is None:
        raise NotFoundException(f"Candidate position {candidate_position_id} not found")

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
    await session.commit()
    await session.refresh(evaluation)

    return evaluation


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

    await eventbridge_service.publish_evaluation_event(
        evaluation_id=evaluation.id,
        candidate_position_id=candidate_position_id,
        step_type=step_type,
        source_document_id=source_document_id,
        rubric_version_id=rubric_version_id,
    )

    return evaluation


async def trigger_feedback_gen(
    session: AsyncSession,
    candidate_position_id: int,
) -> Evaluation:
    return await trigger_evaluation(
        session=session,
        candidate_position_id=candidate_position_id,
        step_type=EvaluationStepType.feedback_gen,
    )


_RECOMMENDATION_CASCADES_FROM: frozenset[EvaluationStepType] = frozenset(
    {
        EvaluationStepType.cv_analysis,
        EvaluationStepType.screening_eval,
        EvaluationStepType.technical_eval,
    }
)

_REQUIRES_COMPLETED_TECHNICAL_EVAL: frozenset[EvaluationStepType] = frozenset(
    {
        EvaluationStepType.cv_analysis,
        EvaluationStepType.screening_eval,
    }
)


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

    rerun = await create_evaluation(
        session=session,
        candidate_position_id=candidate_position_id,
        step_type=step_type,
        source_document_id=latest.source_document_id,
        rubric_version_id=latest.rubric_version_id,
    )

    await eventbridge_service.publish_evaluation_event(
        evaluation_id=rerun.id,
        candidate_position_id=candidate_position_id,
        step_type=step_type,
        source_document_id=rerun.source_document_id,
        rubric_version_id=rerun.rubric_version_id,
    )

    created = [rerun]

    if step not in _RECOMMENDATION_CASCADES_FROM:
        return created

    should_cascade = step == EvaluationStepType.technical_eval

    if not should_cascade:
        completed_technical = await _latest_evaluation_for_step(
            session, candidate_position_id, EvaluationStepType.technical_eval
        )
        should_cascade = (
            completed_technical is not None
            and completed_technical.status == EvaluationStatus.completed
        )

    if not should_cascade:
        return created

    latest_recommendation = await _latest_evaluation_for_step(
        session, candidate_position_id, EvaluationStepType.recommendation
    )
    cascaded = await create_evaluation(
        session=session,
        candidate_position_id=candidate_position_id,
        step_type=EvaluationStepType.recommendation,
        source_document_id=latest_recommendation.source_document_id
        if latest_recommendation
        else None,
        rubric_version_id=latest_recommendation.rubric_version_id
        if latest_recommendation
        else None,
    )

    await eventbridge_service.publish_evaluation_event(
        evaluation_id=cascaded.id,
        candidate_position_id=candidate_position_id,
        step_type=EvaluationStepType.recommendation,
        source_document_id=cascaded.source_document_id,
        rubric_version_id=cascaded.rubric_version_id,
    )

    created.append(cascaded)
    return created
