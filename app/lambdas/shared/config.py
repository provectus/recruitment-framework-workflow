import os

DB_HOST: str = os.environ.get("DB_HOST", "localhost")
DB_PORT: str = os.environ.get("DB_PORT", "5432")
DB_NAME: str = os.environ.get("DB_NAME", "lauter")
DB_USERNAME: str = os.environ.get("DB_USERNAME", "postgres")
DB_PASSWORD: str = os.environ.get("DB_PASSWORD", "postgres")

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
