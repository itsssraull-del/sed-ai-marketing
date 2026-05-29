"""Knowledge base / RAG models"""
import enum
import uuid
from typing import Optional
from sqlalchemy import String, Text, Float, Integer, Boolean, Enum as SAEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app.database import Base


class DocumentType(str, enum.Enum):
    PRODUCT_CATALOGUE = "product_catalogue"
    PRICE_LIST = "price_list"
    DATASHEET = "datasheet"
    BRAND_GUIDELINES = "brand_guidelines"
    SOP = "sop"
    SALES_SCRIPT = "sales_script"
    SUPPLIER_DOC = "supplier_doc"
    INSTALLATION_PHOTO = "installation_photo"
    MARKETING_ASSET = "marketing_asset"
    WHATSAPP_EXPORT = "whatsapp_export"
    SOCIAL_EXPORT = "social_export"
    INDUSTRY_NEWS = "industry_news"
    REGULATION = "regulation"
    COMPANY_INFO = "company_info"
    MISC = "misc"


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    doc_type: Mapped[DocumentType] = mapped_column(SAEnum(DocumentType), default=DocumentType.MISC)

    # Source
    source_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    s3_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Content
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Processing
    is_indexed: Mapped[bool] = mapped_column(Boolean, default=False)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    pinecone_namespace: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Tags
    tags: Mapped[Optional[list]] = mapped_column(ARRAY(String), nullable=True)
    brand_refs: Mapped[Optional[list]] = mapped_column(ARRAY(String), nullable=True)  # e.g., ["Sungrow", "Hinen"]
    product_refs: Mapped[Optional[list]] = mapped_column(ARRAY(String), nullable=True)
    doc_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Auto-refresh
    auto_refresh: Mapped[bool] = mapped_column(Boolean, default=False)
    refresh_interval_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_refreshed: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pinecone_vector_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    doc_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
