from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from shared.models import Evaluation


def fetch_latest_completed_result(
    session: Session,
    candidate_position_id: int,
    step_type: str,
) -> dict[str, Any] | None:
    stmt = (
        select(Evaluation)
        .where(
            Evaluation.candidate_position_id == candidate_position_id,
            Evaluation.step_type == step_type,
            Evaluation.status == "completed",
        )
        .order_by(Evaluation.version.desc())
        .limit(1)
    )
    row = session.execute(stmt).scalar_one_or_none()
    if row is not None:
        return row.result
    return None
