import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import aioboto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings
from app.exceptions import NotFoundException

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _s3_client(*, for_presign: bool = False) -> AsyncIterator[Any]:
    session = aioboto3.Session()
    kwargs: dict[str, str] = {"region_name": settings.s3_region}
    if for_presign and settings.s3_presign_endpoint_url:
        kwargs["endpoint_url"] = settings.s3_presign_endpoint_url
    elif settings.s3_endpoint_url:
        kwargs["endpoint_url"] = settings.s3_endpoint_url
    async with session.client("s3", **kwargs) as client:
        yield client


def _handle_s3_error(err: ClientError, s3_key: str) -> None:
    error_code = err.response.get("Error", {}).get("Code", "")
    if error_code in ("404", "NoSuchKey"):
        raise NotFoundException(f"Object not found: {s3_key}") from err
    raise RuntimeError(f"S3 operation failed for {s3_key}: {err}") from err


async def generate_upload_url(
    s3_key: str,
    content_type: str,
    max_size: int,
) -> str:
    try:
        async with _s3_client(for_presign=True) as s3_client:
            return await s3_client.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": settings.s3_bucket_name,
                    "Key": s3_key,
                    "ContentType": content_type,
                },
                ExpiresIn=900,
                HttpMethod="PUT",
            )
    except ClientError as err:
        _handle_s3_error(err, s3_key)
        raise
    except BotoCoreError as err:
        raise RuntimeError(f"S3 operation failed for {s3_key}: {err}") from err


async def generate_view_url(
    s3_key: str,
    expiration: int = 3600,
) -> str:
    try:
        async with _s3_client(for_presign=True) as s3_client:
            return await s3_client.generate_presigned_url(
                ClientMethod="get_object",
                Params={
                    "Bucket": settings.s3_bucket_name,
                    "Key": s3_key,
                },
                ExpiresIn=expiration,
            )
    except ClientError as err:
        _handle_s3_error(err, s3_key)
        raise
    except BotoCoreError as err:
        raise RuntimeError(f"S3 operation failed for {s3_key}: {err}") from err


async def put_text_object(
    s3_key: str,
    content: str,
    content_type: str,
) -> None:
    try:
        async with _s3_client() as s3_client:
            await s3_client.put_object(
                Bucket=settings.s3_bucket_name,
                Key=s3_key,
                Body=content.encode("utf-8"),
                ContentType=content_type,
            )
    except ClientError as err:
        _handle_s3_error(err, s3_key)
    except BotoCoreError as err:
        raise RuntimeError(f"S3 operation failed for {s3_key}: {err}") from err


async def get_object_size(s3_key: str) -> int:
    try:
        async with _s3_client() as s3_client:
            response = await s3_client.head_object(
                Bucket=settings.s3_bucket_name,
                Key=s3_key,
            )
            return response["ContentLength"]
    except ClientError as err:
        _handle_s3_error(err, s3_key)
        raise
    except BotoCoreError as err:
        raise RuntimeError(f"S3 operation failed for {s3_key}: {err}") from err


async def delete_object(s3_key: str) -> None:
    try:
        async with _s3_client() as s3_client:
            await s3_client.delete_object(
                Bucket=settings.s3_bucket_name,
                Key=s3_key,
            )
    except ClientError as err:
        _handle_s3_error(err, s3_key)
    except BotoCoreError as err:
        raise RuntimeError(f"S3 operation failed for {s3_key}: {err}") from err
