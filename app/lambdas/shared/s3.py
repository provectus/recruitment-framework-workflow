import io

import boto3
import docx
from pypdf import PdfReader

from shared import config

_client = None

_MAX_DOCUMENT_SIZE_BYTES = 50 * 1024 * 1024


def get_client():
    global _client
    if _client is None:
        kwargs = {"region_name": config.AWS_REGION}
        if config.S3_ENDPOINT_URL:
            kwargs["endpoint_url"] = config.S3_ENDPOINT_URL
        _client = boto3.client("s3", **kwargs)
    return _client


def get_document_text(s3_key: str) -> str:
    client = get_client()
    try:
        response = client.get_object(Bucket=config.S3_BUCKET_NAME, Key=s3_key)
        content_length = int(response.get("ContentLength", 0))
        if content_length > _MAX_DOCUMENT_SIZE_BYTES:
            raise ValueError(
                f"Document exceeds maximum allowed size of "
                f"{_MAX_DOCUMENT_SIZE_BYTES // (1024 * 1024)}MB: "
                f"key={s3_key} size={content_length}"
            )
        body = response["Body"].read()
    except client.exceptions.NoSuchKey as exc:
        raise FileNotFoundError(
            f"Document not found in S3: bucket={config.S3_BUCKET_NAME} key={s3_key}"
        ) from exc

    key_lower = s3_key.lower()

    if key_lower.endswith(".pdf"):
        return _extract_pdf_text(body)

    if key_lower.endswith(".docx"):
        return _extract_docx_text(body)

    return body.decode("utf-8")


def _extract_pdf_text(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def _extract_docx_text(data: bytes) -> str:
    doc = docx.Document(io.BytesIO(data))
    paragraphs = [para.text for para in doc.paragraphs]
    return "\n".join(paragraphs)
