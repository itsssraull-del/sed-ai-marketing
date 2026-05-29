"""Content generation, CRUD, and approval workflow routes"""
import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from datetime import datetime, timezone

from app.database import get_db
from app.models.content import ContentItem, ContentStatus, Platform, ContentType
from app.models.user import User
from app.core.security import get_current_user, require_editor, require_manager
from app.agents.orchestrator import get_orchestrator
from app.services.vector_store import get_vector_store

router = APIRouter()


class GenerateContentRequest(BaseModel):
    platform: Platform
    content_type: ContentType
    topic: str
    target_audience: str = "solar installers"
    context: dict = {}
    auto_generate_image: bool = True


class ApproveContentRequest(BaseModel):
    approved: bool
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None


class ScheduleContentRequest(BaseModel):
    scheduled_for: str  # ISO datetime string


class ContentResponse(BaseModel):
    id: str
    title: str
    body: str
    platform: str
    content_type: str
    status: str
    confidence_score: Optional[float]
    image_url: Optional[str]
    video_url: Optional[str]
    hashtags: Optional[List[str]]
    scheduled_for: Optional[str]
    published_at: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


@router.post("/generate")
async def generate_content(
    request: GenerateContentRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor),
):
    """Trigger the AI agent system to generate content"""
    # Fetch RAG context for the topic
    vector_store = get_vector_store()
    rag_context = await vector_store.search_for_content_generation(
        topic=request.topic,
        platform=request.platform.value,
    )

    orchestrator = get_orchestrator()
    result = await orchestrator.run(
        task_type="generate_content",
        platform=request.platform.value,
        content_type=request.content_type.value,
        topic=request.topic,
        target_audience=request.target_audience,
        context={**request.context, "rag_context": rag_context},
    )

    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])

    generated = result.get("content", {})
    if not generated:
        raise HTTPException(status_code=500, detail="Content generation produced no output")

    # Persist to database
    item = ContentItem(
        id=uuid.uuid4(),
        title=generated.get("title", f"{request.platform.value} - {request.topic}"),
        body=generated.get("body", ""),
        caption=generated.get("caption") or generated.get("body", "")[:200],
        hashtags=generated.get("hashtags", []),
        platform=request.platform,
        content_type=request.content_type,
        status=ContentStatus.PENDING_REVIEW if result.get("requires_human_approval") else ContentStatus.APPROVED,
        generating_agent="orchestrator",
        ai_model_used="claude-opus-4-6",
        confidence_score=result.get("confidence_score"),
        requires_approval=result.get("requires_human_approval", True),
        topic_tags=[request.topic],
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)

    # Trigger image generation in background if requested
    if request.auto_generate_image and result.get("design_prompt"):
        from app.workers.tasks import generate_image_task
        background_tasks.add_task(
            generate_image_task.delay,
            result["design_prompt"],
            request.platform.value,
            request.content_type.value,
            str(item.id),
        )

    return {
        "content_id": str(item.id),
        "status": item.status.value,
        "requires_approval": item.requires_approval,
        "confidence_score": item.confidence_score,
        "preview": {
            "title": item.title,
            "body": item.body[:300],
            "hashtags": item.hashtags,
        },
    }


@router.get("/", response_model=List[ContentResponse])
async def list_content(
    platform: Optional[Platform] = None,
    status: Optional[ContentStatus] = None,
    limit: int = Query(default=20, le=100),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = []
    if platform:
        filters.append(ContentItem.platform == platform)
    if status:
        filters.append(ContentItem.status == status)

    result = await db.execute(
        select(ContentItem)
        .where(and_(*filters) if filters else True)
        .order_by(desc(ContentItem.created_at))
        .limit(limit).offset(offset)
    )
    return result.scalars().all()


@router.get("/{content_id}")
async def get_content(
    content_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(ContentItem).where(ContentItem.id == content_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Content not found")
    return item


@router.patch("/{content_id}/approve")
async def approve_content(
    content_id: str,
    request: ApproveContentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    result = await db.execute(select(ContentItem).where(ContentItem.id == content_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Content not found")

    if request.approved:
        item.status = ContentStatus.APPROVED
        item.approved_by = str(current_user.id)
        item.approval_notes = request.notes
    else:
        item.status = ContentStatus.REJECTED
        item.rejection_reason = request.rejection_reason

    await db.commit()
    return {"content_id": content_id, "status": item.status.value}


@router.patch("/{content_id}/schedule")
async def schedule_content(
    content_id: str,
    request: ScheduleContentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    result = await db.execute(select(ContentItem).where(ContentItem.id == content_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Content not found")
    if item.status not in [ContentStatus.APPROVED, ContentStatus.DRAFT]:
        raise HTTPException(status_code=400, detail="Content must be approved before scheduling")

    item.status = ContentStatus.SCHEDULED
    item.scheduled_for = request.scheduled_for
    await db.commit()

    # Register with scheduler
    from app.services.scheduler import get_scheduler
    scheduler = get_scheduler()
    job_id = scheduler.schedule_post(
        content_item_id=content_id,
        scheduled_for=datetime.fromisoformat(request.scheduled_for),
        platform=item.platform.value,
    )

    return {"content_id": content_id, "scheduled_for": request.scheduled_for, "job_id": job_id}


@router.delete("/{content_id}", dependencies=[Depends(require_manager)])
async def delete_content(content_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ContentItem).where(ContentItem.id == content_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Content not found")
    item.status = ContentStatus.ARCHIVED
    await db.commit()
    return {"message": "Content archived"}


@router.post("/{content_id}/regenerate")
async def regenerate_content(
    content_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor),
):
    """Re-run the AI generation for a content item"""
    result = await db.execute(select(ContentItem).where(ContentItem.id == content_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Content not found")

    orchestrator = get_orchestrator()
    new_result = await orchestrator.run(
        task_type="generate_content",
        platform=item.platform.value,
        content_type=item.content_type.value,
        topic=item.topic_tags[0] if item.topic_tags else "general",
    )

    if new_result.get("content"):
        generated = new_result["content"]
        item.body = generated.get("body", item.body)
        item.hashtags = generated.get("hashtags", item.hashtags)
        item.status = ContentStatus.PENDING_REVIEW
        item.version += 1
        item.confidence_score = new_result.get("confidence_score")
        await db.commit()

    return {"content_id": content_id, "version": item.version, "status": item.status.value}
