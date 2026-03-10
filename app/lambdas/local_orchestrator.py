import importlib
import logging
import time

from shared import config
from shared.db import get_session
from shared.models import Evaluation

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("local-orchestrator")

POLL_INTERVAL_SECONDS = 2

HANDLER_MODULES = {
    "cv_analysis": "cv_analysis.handler",
    "screening_eval": "screening_eval.handler",
    "technical_eval": "technical_eval.handler",
    "recommendation": "recommendation.handler",
    "feedback_gen": "feedback_gen.handler",
}


def build_event(evaluation: Evaluation) -> dict:
    return {
        "detail": {
            "evaluation_id": evaluation.id,
            "candidate_position_id": evaluation.candidate_position_id,
            "step_type": evaluation.step_type,
        }
    }


def dispatch(evaluation: Evaluation) -> None:
    step_type = evaluation.step_type
    module_path = HANDLER_MODULES.get(step_type)
    if module_path is None:
        logger.error(f"Unknown step_type: {step_type}")
        return

    module = importlib.import_module(module_path)
    event = build_event(evaluation)

    logger.info(
        f"Dispatching evaluation {evaluation.id} "
        f"(step={step_type}, version={evaluation.version})"
    )

    try:
        module.handler(event, None)
        logger.info(f"Evaluation {evaluation.id} completed")
    except Exception:
        logger.exception(f"Evaluation {evaluation.id} failed")


def poll_and_dispatch() -> None:
    with get_session() as session:
        pending = (
            session.query(Evaluation)
            .filter(Evaluation.status == "pending")
            .order_by(Evaluation.created_at.asc())
            .all()
        )

    for evaluation in pending:
        dispatch(evaluation)


def main() -> None:
    logger.info("Local orchestrator started")
    logger.info(f"  MOCK_BEDROCK={config.MOCK_BEDROCK}")
    logger.info(f"  MOCK_BEDROCK_DELAY_SECONDS={config.MOCK_BEDROCK_DELAY_SECONDS}")
    logger.info(f"  MOCK_EVALUATION_FAILURES={config.MOCK_EVALUATION_FAILURES}")
    logger.info(f"  DB: {config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}")

    while True:
        try:
            poll_and_dispatch()
        except Exception:
            logger.exception("Error during poll cycle")
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
