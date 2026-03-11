from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from shared import db as db_module
from shared.models import Evaluation


@contextmanager
def run_evaluation(
    evaluation_id: int,
) -> Generator[tuple[Session, Evaluation], None, None]:
    with db_module.get_session() as session:
        evaluation = session.get(Evaluation, evaluation_id)
        if evaluation is None:
            raise ValueError(f"Evaluation {evaluation_id} not found")

        try:
            evaluation.status = "running"
            evaluation.started_at = datetime.now(tz=UTC)
            session.add(evaluation)
            session.commit()
            session.refresh(evaluation)

            yield session, evaluation

        except Exception as exc:
            evaluation.status = "failed"
            evaluation.error_message = str(exc)
            evaluation.completed_at = datetime.now(tz=UTC)
            session.add(evaluation)
            session.commit()
            raise


def complete_evaluation(
    session: Session,
    evaluation: Evaluation,
    result: dict[str, Any],
) -> None:
    evaluation.status = "completed"
    evaluation.result = result
    evaluation.completed_at = datetime.now(tz=UTC)
    session.add(evaluation)
    session.commit()
