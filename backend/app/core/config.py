from dataclasses import dataclass
from os import getenv
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_name: str = "HackEval AI API"
    api_prefix: str = "/api"
    jwt_secret: str = getenv("JWT_SECRET", "change-me-in-production")
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 480
    allowed_origins: tuple[str, ...] = tuple(
        value.strip() for value in getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    )
    upload_dir: str = getenv("UPLOAD_DIR", str(Path(__file__).resolve().parents[2] / "uploads"))
    github_token: str = getenv("GITHUB_TOKEN", "")


settings = Settings()
