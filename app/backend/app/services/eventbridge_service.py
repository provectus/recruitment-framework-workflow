import json
import logging

import aioboto3

from app.config import settings

logger = logging.getLogger(__name__)


async def publish_evaluation_event(
    evaluation_id: int,
    candidate_position_id: int,
    step_type: str,
    source_document_id: int | None = None,
    rubric_version_id: int | None = None,
) -> None:
    if not settings.evaluation_event_bus_name:
        return

    detail = {
        "evaluation_id": evaluation_id,
        "candidate_position_id": candidate_position_id,
        "step_type": step_type,
        "source_document_id": source_document_id,
        "rubric_version_id": rubric_version_id,
    }

    try:
        session = aioboto3.Session()
        async with session.client("events", region_name=settings.s3_region) as client:
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
    except Exception:
        logger.warning(
            "Failed to publish evaluation event for evaluation_id=%s step_type=%s",
            evaluation_id,
            step_type,
            exc_info=True,
        )
