import json
import logging
import os

import boto3

logger = logging.getLogger(__name__)

DB_HOST: str = os.environ.get("DB_HOST", "localhost")
DB_PORT: str = os.environ.get("DB_PORT", "5432")
DB_NAME: str = os.environ.get("DB_NAME", "lauter")
DB_USERNAME: str = os.environ.get("DB_USERNAME", "postgres")
DB_PASSWORD_SECRET_ARN: str = os.environ.get("DB_PASSWORD_SECRET_ARN", "")


def _resolve_db_password() -> str:
    env_password = os.environ.get("DB_PASSWORD", "")
    if env_password:
        return env_password
    if not DB_PASSWORD_SECRET_ARN:
        return "postgres"
    try:
        client = boto3.client("secretsmanager")
        resp = client.get_secret_value(SecretId=DB_PASSWORD_SECRET_ARN)
        secret = json.loads(resp["SecretString"])
        return secret.get("password", "")
    except Exception:
        logger.exception("Failed to fetch DB password from Secrets Manager")
        raise


DB_PASSWORD: str = _resolve_db_password()

S3_BUCKET_NAME: str = os.environ.get("S3_BUCKET_NAME", "lauter-files")
BEDROCK_MODEL_ID: str = os.environ.get(
    "BEDROCK_MODEL_ID", "anthropic.claude-sonnet-4-6"
)
AWS_REGION: str = os.environ.get("AWS_REGION", "us-east-1")

S3_ENDPOINT_URL: str = os.environ.get("S3_ENDPOINT_URL", "")
MOCK_BEDROCK: bool = os.environ.get("MOCK_BEDROCK", "").lower() in ("true", "1", "yes")
MOCK_BEDROCK_DELAY_SECONDS: float = float(os.environ.get("MOCK_BEDROCK_DELAY_SECONDS", "3"))
MOCK_EVALUATION_FAILURES: list[str] = [
    s.strip() for s in os.environ.get("MOCK_EVALUATION_FAILURES", "").split(",") if s.strip()
]
