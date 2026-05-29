"""Stock inventory and alert models"""
import enum
import uuid
from typing import Optional
from sqlalchemy import String, Text, Float, Integer, Boolean, Enum as SAEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app.database import Base


class StockStatus(str, enum.Enum):
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    ON_ORDER = "on_order"
    ARRIVING_SOON = "arriving_soon"


class ProductCategory(str, enum.Enum):
    SOLAR_PANEL = "solar_panel"
    INVERTER = "inverter"
    BATTERY = "battery"
    MOUNTING = "mounting"
    ACCESSORY = "accessory"
    BOS = "bos"  # Balance of System


class StockItem(Base):
    __tablename__ = "stock_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Product identity
    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    brand: Mapped[str] = mapped_column(String(100), nullable=False)  # Sungrow, Hinen, Astronergy, etc.
    model: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    category: Mapped[ProductCategory] = mapped_column(SAEnum(ProductCategory), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Technical specs (JSON for flexibility)
    specifications: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    datasheet_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Inventory
    quantity_on_hand: Mapped[int] = mapped_column(Integer, default=0)
    quantity_reserved: Mapped[int] = mapped_column(Integer, default=0)
    quantity_on_order: Mapped[int] = mapped_column(Integer, default=0)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=10)
    status: Mapped[StockStatus] = mapped_column(SAEnum(StockStatus), default=StockStatus.OUT_OF_STOCK)

    # Pricing (exclusive of VAT)
    unit_price_zar: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bulk_price_zar: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    min_order_qty: Mapped[int] = mapped_column(Integer, default=1)

    # Sage / ERP sync
    sage_item_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_sage_sync: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Content generation flags
    auto_generate_content: Mapped[bool] = mapped_column(Boolean, default=True)
    content_generated_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)


class StockAlert(Base):
    __tablename__ = "stock_alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stock_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    alert_type: Mapped[str] = mapped_column(String(100), nullable=False)  # new_arrival, low_stock, restocked
    previous_qty: Mapped[int] = mapped_column(Integer, default=0)
    new_qty: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    content_item_ids: Mapped[Optional[list]] = mapped_column(ARRAY(String), nullable=True)
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
