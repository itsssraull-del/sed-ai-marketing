"""
SED Energy AI Marketing System - Configuration
Central configuration using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    # ─── Application ────────────────────────────────────────────────────────────
    APP_NAME: str = "SED Energy AI Marketing System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    SECRET_KEY: str
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "https://app.sed.energy"]

    # ─── Database ────────────────────────────────────────────────────────────────
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"

    # ─── AI / LLM APIs ──────────────────────────────────────────────────────────
    ANTHROPIC_API_KEY: str
    OPENAI_API_KEY: str
    GEMINI_API_KEY: Optional[str] = None

    # ─── Vector Database ────────────────────────────────────────────────────────
    PINECONE_API_KEY: str
    PINECONE_ENV: str = "us-east-1-aws"
    PINECONE_INDEX_NAME: str = "sed-energy-knowledge"
    PINECONE_DIMENSION: int = 1536

    # ─── Social Media APIs ──────────────────────────────────────────────────────
    # Meta (Facebook + Instagram)
    META_APP_ID: Optional[str] = None
    META_APP_SECRET: Optional[str] = None
    META_ACCESS_TOKEN: Optional[str] = None
    META_PAGE_ID: Optional[str] = None                      # Facebook Page ID
    META_INSTAGRAM_ACCOUNT_ID: Optional[str] = None         # Instagram Business Account ID
    META_GRAPH_API_VERSION: str = "v19.0"

    # LinkedIn
    LINKEDIN_CLIENT_ID: Optional[str] = None
    LINKEDIN_CLIENT_SECRET: Optional[str] = None
    LINKEDIN_ACCESS_TOKEN: Optional[str] = None
    LINKEDIN_ORGANIZATION_ID: Optional[str] = None          # Company page URN

    # WhatsApp Business API
    WHATSAPP_API_TOKEN: Optional[str] = None
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    WHATSAPP_BUSINESS_ACCOUNT_ID: Optional[str] = None
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: Optional[str] = None

    # ─── Image Generation APIs ──────────────────────────────────────────────────
    REPLICATE_API_TOKEN: str               # Flux / SDXL via Replicate
    STABILITY_API_KEY: Optional[str] = None
    IDEOGRAM_API_KEY: Optional[str] = None

    # ─── Video Generation APIs ──────────────────────────────────────────────────
    RUNWAY_API_KEY: Optional[str] = None
    PIKA_API_KEY: Optional[str] = None
    KLING_API_KEY: Optional[str] = None

    # ─── NAS / File Storage ─────────────────────────────────────────────────────
    NAS_HOST: Optional[str] = None
    NAS_PORT: int = 445
    NAS_USERNAME: Optional[str] = None
    NAS_PASSWORD: Optional[str] = None
    NAS_SHARE_NAME: str = "SED-Marketing"
    NAS_SMB_DOMAIN: Optional[str] = None

    # S3-compatible storage (MinIO or AWS S3)
    S3_ENDPOINT_URL: Optional[str] = None
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_BUCKET_NAME: str = "sed-energy-assets"
    S3_REGION: str = "af-south-1"

    # ─── ERP / Sage ─────────────────────────────────────────────────────────────
    SAGE_API_URL: Optional[str] = None
    SAGE_API_KEY: Optional[str] = None
    SAGE_COMPANY_ID: Optional[str] = None

    # ─── News & Industry Feeds ──────────────────────────────────────────────────
    NEWS_API_KEY: Optional[str] = None
    NEWSDATA_API_KEY: Optional[str] = None

    # ─── Email / Notifications ──────────────────────────────────────────────────
    SENDGRID_API_KEY: Optional[str] = None
    NOTIFICATION_EMAIL: str = "admin@sed.energy"
    SLACK_WEBHOOK_URL: Optional[str] = None

    # ─── Auth / Security ────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ─── Rate Limits ────────────────────────────────────────────────────────────
    CONTENT_GENERATION_DAILY_LIMIT: int = 200
    IMAGE_GENERATION_DAILY_LIMIT: int = 100
    VIDEO_GENERATION_DAILY_LIMIT: int = 20

    # ─── SED Branding (read-only reference) ─────────────────────────────────────
    BRAND_PRIMARY_COLOR: str = "#E85A0C"    # SED Orange
    BRAND_SECONDARY_COLOR: str = "#333333"  # SED Dark Grey
    BRAND_ACCENT_COLOR: str = "#FFFFFF"     # White
    BRAND_FONT_PRIMARY: str = "Inter"
    BRAND_COMPANY_NAME: str = "SED Energy"
    BRAND_TAGLINE: str = "South Africa Tier 1 Solar Distributor"
    BRAND_WEBSITE: str = "sed.energy"
    BRAND_EMAIL: str = "info@sed.energy"
    BRAND_PHONE: str = "010 006 8246"
    BRAND_WHATSAPP: str = "+27 79 748 6483"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
