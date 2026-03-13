import json
import logging

import aioboto3

from app.config import settings

logger = logging.getLogger(__name__)

_session = aioboto3.Session()


async def publish_evaluation_event(
    evaluation_id: int,
    candidate_position_id: int,
    step_type: str,
    source_document_id: int | None = None,
    rubric_version_id: int | None = None,
) -> None:
    if not settings.evaluation_event_bus_name:
        if settings.debug:
            logger.info(
                "EventBridge skipped (no bus name configured, DEBUG=true) — "
                "evaluation_id=%s step_type=%s",
                evaluation_id,
                step_type,
            )
            return
        raise RuntimeError(
            f"EVALUATION_EVENT_BUS_NAME is not configured — cannot publish event "
            f"for evaluation_id={evaluation_id} step_type={step_type}"
        )

    detail = {
        "evaluation_id": evaluation_id,
        "candidate_position_id": candidate_position_id,
        "step_type": step_type,
        "source_document_id": source_document_id,
        "rubric_version_id": rubric_version_id,
    }

    async with _session.client("events", region_name=settings.s3_region) as client:
        await client.put_events(
            Entries=[
                {
                    "Source": "lauter.api",
                    "DetailType": "evaluation.requested",
                    "Detail": json.dumps(detail),
                    "EventBusName": settings.evaluation_event_bus_name,
                }
            ]
        )
