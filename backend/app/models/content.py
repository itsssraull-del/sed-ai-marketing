"""Content generation and scheduling models"""
import enum
import uuid
from typing import Optional
from sqlalchemy import String, Text, Float, Integer, Boolean, ForeignKey, Enum as SAEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app.database import Base


class Platform(str, enum.Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    WHATSAPP = "whatsapp"
    TIKTOK = "tiktok"


class ContentType(str, enum.Enum):
    TEXT_POST = "text_post"
    IMAGE_POST = "image_post"
    CAROUSEL = "carousel"
    VIDEO = "video"
    REEL = "reel"
    STORY = "story"
    ARTICLE = "article"
    WHATSAPP_MESSAGE = "whatsapp_message"


class ContentStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class ContentTone(str, enum.Enum):
    PROFESSIONAL = "professional"
    EDUCATIONAL = "educational"
    PROMOTIONAL = "promotional"
    TECHNICAL = "technical"
    EXECUTIVE = "executive"
    CONVERSATIONAL = "conversational"
    URGENT = "urgent"


class ContentItem(Base):
    __tablename__ = "content_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Core content fields
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hashtags: Mapped[Optional[list]] = mapped_column(ARRAY(String), nullable=True)

    # Classification
    platform: Mapped[Platform] = mapped_column(SAEnum(Platform), nullable=False)
    content_type: Mapped[ContentType] = mapped_column(SAEnum(ContentType), nullable=False)
    tone: Mapped[ContentTone] = mapped_column(SAEnum(ContentTone), default=ContentTone.PROFESSIONAL)
    status: Mapped[ContentStatus] = mapped_column(SAEnum(ContentStatus), default=ContentStatus.DRAFT)

    # AI metadata
    generating_agent: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ai_model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    generation_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=True)

    # Media
    image_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    video_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    media_assets: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # carousel images etc

    # Scheduling
    scheduled_for: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    published_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    platform_post_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # WhatsApp-specific
    whatsapp_group_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    whatsapp_group_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Context & tags
    topic_tags: Mapped[Optional[list]] = mapped_column(ARRAY(String), nullable=True)
    product_refs: Mapped[Optional[list]] = mapped_column(ARRAY(String), nullable=True)  # product SKUs
    campaign_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_trigger: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # e.g., "stock_arrival"

    # Approval workflow
    approved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    approval_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Version control
    version: Mapped[int] = mapped_column(Integer, default=1)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("content_items.id"), nullable=True)

    # Analytics (populated after publishing)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    reach: Mapped[int] = mapped_column(Integer, default=0)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    engagement_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    performance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
