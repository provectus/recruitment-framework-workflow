from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    app_name: str = "backend"
    debug: bool = False
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/tap"

    jwt_secret_key: str = "dev-secret-change-in-production"
    cors_origins: list[str] = ["http://localhost:5173"]
    cookie_domain: str | None = None
    cookie_secure: bool = False
    allowed_email_domain: str = "provectus.com"

    cognito_user_pool_id: str = ""
    cognito_client_id: str = ""
    cognito_client_secret: str = ""
    cognito_domain: str = ""
    cognito_redirect_uri: str = "http://localhost:8000/auth/callback"

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


settings = Settings()
