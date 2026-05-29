"""Stock inventory management and alert routes"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.models.stock import StockItem, StockAlert, StockStatus, ProductCategory
from app.models.user import User
from app.core.security import get_current_user, require_manager
from app.agents.stock_agent import StockAgent
from app.agents.orchestrator import get_orchestrator

router = APIRouter()


class StockItemCreate(BaseModel):
    sku: str
    name: str
    brand: str
    model: Optional[str] = None
    category: ProductCategory
    description: Optional[str] = None
    quantity_on_hand: int = 0
    unit_price_zar: Optional[float] = None
    specifications: Optional[dict] = None
    low_stock_threshold: int = 10
    auto_generate_content: bool = True


class StockUpdateRequest(BaseModel):
    quantity_on_hand: int
    trigger_content: bool = True


@router.get("/")
async def list_stock(
    category: Optional[ProductCategory] = None,
    brand: Optional[str] = None,
    status: Optional[StockStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = []
    from sqlalchemy import and_
    if category:
        filters.append(StockItem.category == category)
    if brand:
        filters.append(StockItem.brand == brand)
    if status:
        filters.append(StockItem.status == status)

    result = await db.execute(
        select(StockItem)
        .where(and_(*filters) if filters else True)
        .order_by(StockItem.brand, StockItem.name)
    )
    items = result.scalars().all()
    return [
        {
            "id": str(i.id),
            "sku": i.sku,
            "name": i.name,
            "brand": i.brand,
            "category": i.category.value,
            "status": i.status.value,
            "quantity_on_hand": i.quantity_on_hand,
            "quantity_reserved": i.quantity_reserved,
            "low_stock_threshold": i.low_stock_threshold,
            "unit_price_zar": i.unit_price_zar,
            "image_url": i.image_url,
            "is_featured": i.is_featured,
        }
        for i in items
    ]


@router.post("/", dependencies=[Depends(require_manager)])
async def create_stock_item(
    data: StockItemCreate,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(StockItem).where(StockItem.sku == data.sku))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"SKU {data.sku} already exists")

    # Determine initial status
    if data.quantity_on_hand == 0:
        status = StockStatus.OUT_OF_STOCK
    elif data.quantity_on_hand <= data.low_stock_threshold:
        status = StockStatus.LOW_STOCK
    else:
        status = StockStatus.IN_STOCK

    item = StockItem(
        id=uuid.uuid4(),
        sku=data.sku,
        name=data.name,
        brand=data.brand,
        model=data.model,
        category=data.category,
        description=data.description,
        quantity_on_hand=data.quantity_on_hand,
        unit_price_zar=data.unit_price_zar,
        specifications=data.specifications,
        low_stock_threshold=data.low_stock_threshold,
        auto_generate_content=data.auto_generate_content,
        status=status,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return {"id": str(item.id), "sku": item.sku, "status": item.status.value}


@router.patch("/{item_id}/quantity")
async def update_stock_quantity(
    item_id: str,
    request: StockUpdateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    result = await db.execute(select(StockItem).where(StockItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Stock item not found")

    previous_qty = item.quantity_on_hand
    new_qty = request.quantity_on_hand

    # Determine alert type
    alert_type = None
    if previous_qty == 0 and new_qty > 0:
        alert_type = "new_arrival"
    elif previous_qty > 0 and new_qty == 0:
        alert_type = "out_of_stock"
    elif new_qty <= item.low_stock_threshold:
        alert_type = "low_stock"
    elif new_qty > previous_qty:
        alert_type = "back_in_stock" if previous_qty < item.low_stock_threshold else "restocked"

    # Update status
    if new_qty == 0:
        item.status = StockStatus.OUT_OF_STOCK
    elif new_qty <= item.low_stock_threshold:
        item.status = StockStatus.LOW_STOCK
    else:
        item.status = StockStatus.IN_STOCK
    item.quantity_on_hand = new_qty

    # Create alert record
    if alert_type:
        alert = StockAlert(
            id=uuid.uuid4(),
            stock_item_id=item.id,
            alert_type=alert_type,
            previous_qty=previous_qty,
            new_qty=new_qty,
        )
        db.add(alert)

    await db.commit()

    # Trigger content generation if configured
    if request.trigger_content and alert_type in ["new_arrival", "back_in_stock"] and item.auto_generate_content:
        background_tasks.add_task(
            _trigger_stock_content,
            item_data={
                "product_name": item.name,
                "brand": item.brand,
                "sku": item.sku,
                "quantity": new_qty,
                "category": item.category.value,
                "alert_type": alert_type,
            }
        )

    return {
        "sku": item.sku,
        "previous_qty": previous_qty,
        "new_qty": new_qty,
        "new_status": item.status.value,
        "alert_type": alert_type,
        "content_triggered": request.trigger_content and alert_type in ["new_arrival", "back_in_stock"],
    }


async def _trigger_stock_content(item_data: dict):
    orchestrator = get_orchestrator()
    for platform in ["facebook", "whatsapp", "linkedin"]:
        await orchestrator.run(
            task_type="stock_alert",
            platform=platform,
            context={"stock_event": {**item_data}},
        )


@router.get("/alerts")
async def get_stock_alerts(
    processed: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = []
    from sqlalchemy import and_
    if processed is not None:
        filters.append(StockAlert.is_processed == processed)

    result = await db.execute(
        select(StockAlert)
        .where(and_(*filters) if filters else True)
        .order_by(desc(StockAlert.created_at))
        .limit(50)
    )
    alerts = result.scalars().all()
    return [
        {
            "id": str(a.id),
            "stock_item_id": str(a.stock_item_id),
            "alert_type": a.alert_type,
            "previous_qty": a.previous_qty,
            "new_qty": a.new_qty,
            "content_triggered": a.content_triggered,
            "is_processed": a.is_processed,
            "created_at": str(a.created_at),
        }
        for a in alerts
    ]


@router.post("/sage-sync", dependencies=[Depends(require_manager)])
async def trigger_sage_sync(background_tasks: BackgroundTasks):
    """Trigger a manual Sage ERP stock sync"""
    background_tasks.add_task(_run_sage_sync)
    return {"message": "Sage sync triggered"}


async def _run_sage_sync():
    from app.workers.tasks import check_stock_updates
    await check_stock_updates()
