from dataclasses import dataclass
from os import getenv
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_name: str = "HackEval AI API"
    environment: str = getenv("APP_ENV", "development").lower()
    api_prefix: str = "/api"
    jwt_secret: str = getenv("JWT_SECRET", "change-me-in-production")
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 480
    allowed_origins: tuple[str, ...] = tuple(
        value.strip() for value in getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    )
    upload_dir: str = getenv("UPLOAD_DIR", str(Path(__file__).resolve().parents[2] / "uploads"))
    github_token: str = getenv("GITHUB_TOKEN", "")

    def validate(self) -> None:
        if self.environment in {"production", "staging"} and (
            not self.jwt_secret or self.jwt_secret == "change-me-in-production"
        ):
            raise RuntimeError("JWT_SECRET must be configured outside development")
        if not self.allowed_origins or any(not origin for origin in self.allowed_origins):
            raise RuntimeError("ALLOWED_ORIGINS must contain at least one valid origin")


settings = Settings()
