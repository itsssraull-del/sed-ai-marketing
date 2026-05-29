"""WhatsApp group management, message generation, and webhook routes"""
import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.social import WhatsAppGroup, WhatsAppGroupType
from app.models.user import User
from app.core.security import get_current_user, require_manager
from app.agents.whatsapp_agent import WhatsAppAgent
from app.services.whatsapp_service import WhatsAppService
from app.config import settings

router = APIRouter()


class GroupCreate(BaseModel):
    group_name: str
    group_id: str
    group_type: WhatsAppGroupType
    description: Optional[str] = None
    member_count: int = 0
    posting_frequency_hours: int = 48
    preferred_posting_times: List[str] = ["08:00", "12:00"]
    content_focus: List[str] = []
    custom_instructions: Optional[str] = None


class GenerateMessageRequest(BaseModel):
    group_id: str
    topic: str
    context: dict = {}


class SendMessageRequest(BaseModel):
    group_id: str
    message: str
    phone_numbers: List[str]  # List of recipient numbers for broadcast


@router.get("/groups")
async def list_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(WhatsAppGroup).where(WhatsAppGroup.is_active == True))
    groups = result.scalars().all()
    return [
        {
            "id": str(g.id),
            "group_name": g.group_name,
            "group_type": g.group_type.value,
            "description": g.description,
            "member_count": g.member_count,
            "posting_frequency_hours": g.posting_frequency_hours,
            "last_posted_at": g.last_posted_at,
            "total_messages_sent": g.total_messages_sent,
        }
        for g in groups
    ]


@router.post("/groups")
async def create_group(
    data: GroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    group = WhatsAppGroup(
        id=uuid.uuid4(),
        group_name=data.group_name,
        group_id=data.group_id,
        group_type=data.group_type,
        description=data.description,
        member_count=data.member_count,
        posting_frequency_hours=data.posting_frequency_hours,
        preferred_posting_times=data.preferred_posting_times,
        content_focus=data.content_focus,
        custom_instructions=data.custom_instructions,
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return {"id": str(group.id), "group_name": group.group_name}


@router.post("/generate-message")
async def generate_whatsapp_message(
    request: GenerateMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    """Generate a group-specific WhatsApp message using the AI agent"""
    result = await db.execute(
        select(WhatsAppGroup).where(WhatsAppGroup.group_id == request.group_id)
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="WhatsApp group not found")

    agent = WhatsAppAgent()
    state = {
        "topic": request.topic,
        "platform": "whatsapp",
        "context": {
            **request.context,
            "group_type": group.group_type.value,
            "group_name": group.group_name,
            "custom_instructions": group.custom_instructions,
        },
        "generated_content": None,
    }
    result_data = await agent.run(state)
    message = result_data.get("generated_content", {}).get("whatsapp_message", "")

    return {
        "group_id": request.group_id,
        "group_name": group.group_name,
        "message": message,
        "confidence_score": result_data.get("confidence_score", 0.0),
        "requires_approval": True,
    }


@router.post("/generate-bulk")
async def generate_bulk_messages(
    topic: str,
    context: dict = {},
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    """Generate tailored messages for all active WhatsApp groups"""
    result = await db.execute(select(WhatsAppGroup).where(WhatsAppGroup.is_active == True))
    groups = result.scalars().all()

    agent = WhatsAppAgent()
    messages = await agent.generate_bulk_messages(
        groups=[{"id": str(g.id), "type": g.group_type.value, "name": g.group_name} for g in groups],
        topic=topic,
        context=context,
    )
    return {"generated": len(messages), "messages": messages}


@router.post("/send", dependencies=[Depends(require_manager)])
async def send_whatsapp_message(
    request: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send an approved WhatsApp message to a broadcast list"""
    service = WhatsAppService()
    results = await service.send_to_group_broadcast(
        phone_numbers=request.phone_numbers,
        message=request.message,
    )
    sent_count = sum(1 for r in results if r.get("success"))

    # Update group stats
    result = await db.execute(
        select(WhatsAppGroup).where(WhatsAppGroup.group_id == request.group_id)
    )
    group = result.scalar_one_or_none()
    if group:
        from datetime import datetime, timezone
        group.last_posted_at = datetime.now(timezone.utc).isoformat()
        group.total_messages_sent += sent_count
        await db.commit()

    return {"sent": sent_count, "total": len(request.phone_numbers), "results": results}


@router.get("/webhook")
async def verify_whatsapp_webhook(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge"),
):
    """Meta webhook verification endpoint"""
    service = WhatsAppService()
    result = await service.verify_webhook(mode, token, challenge)
    if result:
        return int(result)
    raise HTTPException(status_code=403, detail="Webhook verification failed")


@router.post("/webhook")
async def process_whatsapp_webhook(request: Request):
    """Process incoming WhatsApp messages"""
    data = await request.json()
    service = WhatsAppService()
    events = await service.process_webhook(data)
    # TODO: Route events to engagement agent for reply suggestions
    return {"processed": len(events)}
