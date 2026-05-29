"""User and authentication models"""
import enum
import uuid
from sqlalchemy import String, Boolean, Enum as SAEnum, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MARKETING_MANAGER = "marketing_manager"
    CONTENT_EDITOR = "content_editor"
    VIEWER = "viewer"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.CONTENT_EDITOR)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notification_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    slack_user_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_login: Mapped[str | None] = mapped_column(String(50), nullable=True)
    preferences: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string
