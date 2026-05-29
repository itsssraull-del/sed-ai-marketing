"""Social media publishing and scheduling routes"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.models.content import ContentItem, ContentStatus, Platform
from app.models.user import User
from app.core.security import get_current_user, require_manager
from app.services.social_publisher import SocialPublisherService

router = APIRouter()


class PublishNowRequest(BaseModel):
    content_item_id: str


class CalendarResponse(BaseModel):
    date: str
    platform: str
    content_id: str
    title: str
    status: str
    scheduled_for: Optional[str]


@router.post("/publish-now", dependencies=[Depends(require_manager)])
async def publish_now(
    request: PublishNowRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Immediately publish an approved content item"""
    result = await db.execute(
        select(ContentItem).where(ContentItem.id == request.content_item_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Content item not found")
    if item.status != ContentStatus.APPROVED:
        raise HTTPException(status_code=400, detail=f"Content must be APPROVED. Current status: {item.status.value}")

    publisher = SocialPublisherService()
    publish_result = await publisher.publish({
        "platform": item.platform.value,
        "body": item.body,
        "caption": item.caption,
        "image_url": item.image_url,
        "video_url": item.video_url,
        "content_type": item.content_type.value,
    })

    if publish_result.get("success"):
        from datetime import datetime, timezone
        item.status = ContentStatus.PUBLISHED
        item.platform_post_id = publish_result.get("post_id")
        item.published_at = datetime.now(timezone.utc).isoformat()
        await db.commit()
        return {"success": True, "post_id": publish_result.get("post_id"), "platform": item.platform.value}
    else:
        item.status = ContentStatus.FAILED
        await db.commit()
        raise HTTPException(status_code=500, detail=publish_result.get("error", "Publish failed"))


@router.get("/calendar")
async def get_content_calendar(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get upcoming scheduled content for all platforms"""
    result = await db.execute(
        select(ContentItem)
        .where(ContentItem.status.in_([ContentStatus.SCHEDULED, ContentStatus.APPROVED]))
        .order_by(ContentItem.scheduled_for)
        .limit(50)
    )
    items = result.scalars().all()
    return [
        {
            "id": str(i.id),
            "title": i.title,
            "platform": i.platform.value,
            "content_type": i.content_type.value,
            "status": i.status.value,
            "scheduled_for": i.scheduled_for,
            "image_url": i.image_url,
            "confidence_score": i.confidence_score,
        }
        for i in items
    ]


@router.get("/published")
async def get_published_posts(
    platform: Optional[Platform] = None,
    limit: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get recently published posts with analytics"""
    filters = [ContentItem.status == ContentStatus.PUBLISHED]
    if platform:
        filters.append(ContentItem.platform == platform)

    from sqlalchemy import and_
    result = await db.execute(
        select(ContentItem)
        .where(and_(*filters))
        .order_by(desc(ContentItem.published_at))
        .limit(limit)
    )
    items = result.scalars().all()
    return [
        {
            "id": str(i.id),
            "title": i.title,
            "platform": i.platform.value,
            "published_at": i.published_at,
            "platform_post_id": i.platform_post_id,
            "engagement": {
                "likes": i.likes,
                "comments": i.comments,
                "shares": i.shares,
                "reach": i.reach,
                "engagement_rate": i.engagement_rate,
            },
        }
        for i in items
    ]


@router.get("/pending-approval")
async def get_pending_approval(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all content pending human review"""
    result = await db.execute(
        select(ContentItem)
        .where(ContentItem.status == ContentStatus.PENDING_REVIEW)
        .order_by(desc(ContentItem.created_at))
    )
    items = result.scalars().all()
    return [
        {
            "id": str(i.id),
            "title": i.title,
            "platform": i.platform.value,
            "content_type": i.content_type.value,
            "body": i.body[:500],
            "hashtags": i.hashtags,
            "confidence_score": i.confidence_score,
            "image_url": i.image_url,
            "created_at": str(i.created_at),
            "topic_tags": i.topic_tags,
        }
        for i in items
    ]


@router.get("/stats")
async def get_social_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get overview stats for the dashboard"""
    from sqlalchemy import func
    counts = {}
    for platform in Platform:
        r = await db.execute(
            select(func.count(ContentItem.id)).where(
                ContentItem.platform == platform,
                ContentItem.status == ContentStatus.PUBLISHED,
            )
        )
        counts[platform.value] = r.scalar() or 0

    pending = await db.execute(
        select(func.count(ContentItem.id)).where(ContentItem.status == ContentStatus.PENDING_REVIEW)
    )
    scheduled = await db.execute(
        select(func.count(ContentItem.id)).where(ContentItem.status == ContentStatus.SCHEDULED)
    )

    return {
        "published_by_platform": counts,
        "pending_approval": pending.scalar() or 0,
        "scheduled": scheduled.scalar() or 0,
    }
