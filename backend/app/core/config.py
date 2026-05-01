from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import List
import secrets
import json


class Settings(BaseSettings):
    # ─── App ──────────────────────────────────────────────────────────────────
    APP_NAME: str = "AINTORA SYSTEMS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # ─── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://aintora:aintora_pass@localhost:5432/aintora_db"
    DATABASE_URL_SYNC: str = "postgresql://aintora:aintora_pass@localhost:5432/aintora_db"

    # ─── WhatsApp Cloud API ───────────────────────────────────────────────────
    META_VERIFY_TOKEN: str = "aintora_verify_token_change_me"
    META_APP_SECRET: str = ""
    DEFAULT_WHATSAPP_PHONE_ID: str = ""
    DEFAULT_WHATSAPP_TOKEN: str = ""

    # ─── CORS — stored as plain string, parsed by validator below ─────────────
    # Do NOT put ALLOWED_ORIGINS in your .env file — delete that line if present
    ALLOWED_ORIGINS_STR: str = "http://localhost:3000,http://localhost:5173,https://app.aintora.com"
    ALLOWED_ORIGINS: List[str] = []

    @model_validator(mode="after")
    def build_allowed_origins(self) -> "Settings":
        raw = self.ALLOWED_ORIGINS_STR.strip()
        if raw.startswith("["):
            try:
                self.ALLOWED_ORIGINS = json.loads(raw)
                return self
            except Exception:
                pass
        self.ALLOWED_ORIGINS = [x.strip() for x in raw.split(",") if x.strip()]
        return self

    # ─── Super Admin ──────────────────────────────────────────────────────────
    SUPER_ADMIN_EMAIL: str = "admin@aintora.com"
    SUPER_ADMIN_PASSWORD: str = "Admin2024x"

    # ─── Pagination ───────────────────────────────────────────────────────────
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # ─── Logging ──────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()