"""Social media scheduling and analytics models"""
import enum
import uuid
from typing import Optional
from sqlalchemy import String, Text, Float, Integer, Boolean, Enum as SAEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app.database import Base


class WhatsAppGroupType(str, enum.Enum):
    INSTALLER = "installer"
    VIP_CLIENT = "vip_client"
    INTERNAL_SALES = "internal_sales"
    EPC = "epc"
    REGIONAL_INSTALLER = "regional_installer"
    SUPPLIER = "supplier"
    GENERAL_TRADE = "general_trade"


class WhatsAppGroup(Base):
    __tablename__ = "whatsapp_groups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_name: Mapped[str] = mapped_column(String(255), nullable=False)
    group_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    group_type: Mapped[WhatsAppGroupType] = mapped_column(SAEnum(WhatsAppGroupType), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    member_count: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Posting rules (AI guidance)
    posting_frequency_hours: Mapped[int] = mapped_column(Integer, default=48)
    preferred_posting_times: Mapped[Optional[list]] = mapped_column(ARRAY(String), nullable=True)  # e.g. ["08:00", "12:00"]
    content_focus: Mapped[Optional[list]] = mapped_column(ARRAY(String), nullable=True)
    tone_override: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    product_categories: Mapped[Optional[list]] = mapped_column(ARRAY(String), nullable=True)
    custom_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_posted_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Learning
    avg_engagement_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_messages_sent: Mapped[int] = mapped_column(Integer, default=0)
    message_history_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class ScheduledPost(Base):
    __tablename__ = "scheduled_posts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    scheduled_for: Mapped[str] = mapped_column(String(50), nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    platform_post_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)


class PostAnalytics(Base):
    __tablename__ = "post_analytics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    platform_post_id: Mapped[str] = mapped_column(String(255), nullable=False)

    # Engagement metrics
    likes: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    saves: Mapped[int] = mapped_column(Integer, default=0)
    reach: Mapped[int] = mapped_column(Integer, default=0)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    video_views: Mapped[int] = mapped_column(Integer, default=0)

    # Computed
    engagement_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    performance_label: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # high/medium/low

    # Raw data snapshot
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    fetched_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
