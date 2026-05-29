"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000
"""
from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("role", sa.String(50), server_default="viewer", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    # Content items
    op.create_table(
        "content_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("hashtags", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("content_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), server_default="draft", nullable=False),
        sa.Column("tone", sa.String(50), nullable=True),
        sa.Column("topic", sa.String(255), nullable=True),
        sa.Column("audience", sa.String(100), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("requires_approval", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("has_pricing", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("has_specs", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("image_url", sa.String(1000), nullable=True),
        sa.Column("image_prompt", sa.Text(), nullable=True),
        sa.Column("video_url", sa.String(1000), nullable=True),
        sa.Column("video_script", sa.Text(), nullable=True),
        sa.Column("external_post_id", sa.String(255), nullable=True),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("likes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("comments", sa.Integer(), server_default="0", nullable=False),
        sa.Column("shares", sa.Integer(), server_default="0", nullable=False),
        sa.Column("reach", sa.Integer(), server_default="0", nullable=False),
        sa.Column("impressions", sa.Integer(), server_default="0", nullable=False),
        sa.Column("engagement_rate", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("brand_check_passed", sa.Boolean(), nullable=True),
        sa.Column("brand_check_notes", sa.Text(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("approved_by", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_content_status", "content_items", ["status"])
    op.create_index("ix_content_platform", "content_items", ["platform"])
    op.create_index("ix_content_scheduled", "content_items", ["scheduled_for"])

    # Knowledge documents
    op.create_table(
        "knowledge_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("doc_type", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("s3_key", sa.String(1000), nullable=True),
        sa.Column("chunk_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(50), server_default="pending", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Stock items
    op.create_table(
        "stock_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("sku", sa.String(100), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("brand", sa.String(100), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("quantity", sa.Integer(), server_default="0", nullable=False),
        sa.Column("previous_quantity", sa.Integer(), server_default="0", nullable=False),
        sa.Column("unit_price", sa.Float(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("specifications", postgresql.JSONB(), nullable=True),
        sa.Column("content_generated", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sku"),
    )

    # WhatsApp messages
    op.create_table(
        "whatsapp_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("group_id", sa.String(255), nullable=False),
        sa.Column("group_type", sa.String(50), nullable=False),
        sa.Column("message_body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(50), server_default="draft", nullable=False),
        sa.Column("trigger_type", sa.String(100), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Social accounts
    op.create_table(
        "social_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("account_name", sa.String(255), nullable=False),
        sa.Column("account_id", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("social_accounts")
    op.drop_table("whatsapp_messages")
    op.drop_table("stock_items")
    op.drop_table("knowledge_documents")
    op.drop_index("ix_content_scheduled", "content_items")
    op.drop_index("ix_content_platform", "content_items")
    op.drop_index("ix_content_status", "content_items")
    op.drop_table("content_items")
    op.drop_table("users")
