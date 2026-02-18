from pydantic import model_validator
from pydantic_settings import BaseSettings

_DEV_JWT_SECRET = "dev-secret-change-in-production"


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    app_name: str = "backend"
    debug: bool = False
    database_url: str = ""

    db_host: str = ""
    db_port: int = 5432
    db_name: str = ""
    db_username: str = ""
    db_password: str = ""

    jwt_secret_key: str = _DEV_JWT_SECRET
    cors_origins: list[str] = ["http://localhost:5173"]
    cookie_domain: str | None = None
    cookie_secure: bool = False
    allowed_email_domain: str = "provectus.com"

    cognito_user_pool_id: str = ""
    cognito_client_id: str = ""
    cognito_client_secret: str = ""
    cognito_domain: str = ""
    cognito_redirect_uri: str = "http://localhost:8000/api/auth/callback"

    s3_bucket_name: str = ""
    s3_region: str = "us-east-1"
    s3_endpoint_url: str | None = None
    s3_presign_endpoint_url: str | None = None

    @property
    def cognito_region(self) -> str:
        return (
            self.cognito_user_pool_id.split("_")[0] if self.cognito_user_pool_id else ""
        )

    @property
    def cognito_jwks_url(self) -> str:
        return f"https://cognito-idp.{self.cognito_region}.amazonaws.com/{self.cognito_user_pool_id}/.well-known/jwks.json"

    @property
    def cognito_issuer(self) -> str:
        return f"https://cognito-idp.{self.cognito_region}.amazonaws.com/{self.cognito_user_pool_id}"

    @model_validator(mode="after")
    def _build_database_url_from_parts(self) -> "Settings":
        if not self.database_url and self.db_host:
            self.database_url = (
                f"postgresql+asyncpg://{self.db_username}:{self.db_password}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}"
            )
        if not self.database_url:
            self.database_url = (
                "postgresql+asyncpg://postgres:postgres@localhost:5432/tap"
            )
        return self

    @model_validator(mode="after")
    def _validate_jwt_secret_in_production(self) -> "Settings":
        if not self.debug and self.jwt_secret_key == _DEV_JWT_SECRET:
            msg = "JWT_SECRET_KEY must be changed from the default"
            msg += " in production (DEBUG=false)"
            raise ValueError(msg)
        return self


settings = Settings()
