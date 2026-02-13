from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import aioboto3

from app.config import settings


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


async def generate_upload_url(
    s3_key: str,
    content_type: str,
    max_size: int,
) -> str:
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


async def generate_view_url(
    s3_key: str,
    expiration: int = 3600,
) -> str:
    async with _s3_client(for_presign=True) as s3_client:
        return await s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": settings.s3_bucket_name,
                "Key": s3_key,
            },
            ExpiresIn=expiration,
        )


async def put_text_object(
    s3_key: str,
    content: str,
    content_type: str,
) -> None:
    async with _s3_client() as s3_client:
        await s3_client.put_object(
            Bucket=settings.s3_bucket_name,
            Key=s3_key,
            Body=content.encode("utf-8"),
            ContentType=content_type,
        )


async def delete_object(s3_key: str) -> None:
    async with _s3_client() as s3_client:
        await s3_client.delete_object(
            Bucket=settings.s3_bucket_name,
            Key=s3_key,
        )
