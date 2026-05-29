"""Analytics and performance reporting routes"""
from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.database import get_db
from app.models.content import ContentItem, ContentStatus, Platform
from app.models.user import User
from app.core.security import get_current_user
from app.agents.analytics_agent import AnalyticsAgent

router = APIRouter()


@router.get("/overview")
async def get_analytics_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dashboard analytics overview"""
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    week_ago = (now - timedelta(days=7)).isoformat()
    month_ago = (now - timedelta(days=30)).isoformat()

    total_published = await db.execute(
        select(func.count(ContentItem.id)).where(ContentItem.status == ContentStatus.PUBLISHED)
    )
    published_this_week = await db.execute(
        select(func.count(ContentItem.id)).where(
            ContentItem.status == ContentStatus.PUBLISHED,
            ContentItem.published_at >= week_ago,
        )
    )
    pending = await db.execute(
        select(func.count(ContentItem.id)).where(ContentItem.status == ContentStatus.PENDING_REVIEW)
    )
    avg_confidence = await db.execute(
        select(func.avg(ContentItem.confidence_score)).where(
            ContentItem.confidence_score.isnot(None)
        )
    )
    total_reach = await db.execute(
        select(func.sum(ContentItem.reach)).where(ContentItem.reach > 0)
    )
    total_engagement = await db.execute(
        select(func.sum(ContentItem.likes + ContentItem.comments + ContentItem.shares))
        .where(ContentItem.status == ContentStatus.PUBLISHED)
    )

    return {
        "total_published": total_published.scalar() or 0,
        "published_this_week": published_this_week.scalar() or 0,
        "pending_approval": pending.scalar() or 0,
        "avg_ai_confidence": round(float(avg_confidence.scalar() or 0), 2),
        "total_reach": total_reach.scalar() or 0,
        "total_engagement": total_engagement.scalar() or 0,
    }


@router.get("/top-content")
async def get_top_content(
    platform: Optional[Platform] = None,
    limit: int = Query(default=10, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get highest-performing published content"""
    filters = [ContentItem.status == ContentStatus.PUBLISHED, ContentItem.reach > 0]
    if platform:
        filters.append(ContentItem.platform == platform)

    from sqlalchemy import and_
    result = await db.execute(
        select(ContentItem)
        .where(and_(*filters))
        .order_by(desc(ContentItem.engagement_rate))
        .limit(limit)
    )
    items = result.scalars().all()
    return [
        {
            "id": str(i.id),
            "title": i.title,
            "platform": i.platform.value,
            "content_type": i.content_type.value,
            "published_at": i.published_at,
            "topic_tags": i.topic_tags,
            "engagement": {
                "likes": i.likes, "comments": i.comments,
                "shares": i.shares, "reach": i.reach,
                "engagement_rate": i.engagement_rate,
                "performance_score": i.performance_score,
            },
        }
        for i in items
    ]


@router.get("/platform-breakdown")
async def get_platform_breakdown(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Engagement breakdown by platform"""
    results = {}
    for platform in Platform:
        r = await db.execute(
            select(
                func.count(ContentItem.id).label("post_count"),
                func.avg(ContentItem.engagement_rate).label("avg_engagement"),
                func.sum(ContentItem.reach).label("total_reach"),
                func.sum(ContentItem.likes).label("total_likes"),
            ).where(
                ContentItem.platform == platform,
                ContentItem.status == ContentStatus.PUBLISHED,
            )
        )
        row = r.one()
        results[platform.value] = {
            "post_count": row.post_count or 0,
            "avg_engagement_rate": round(float(row.avg_engagement or 0), 2),
            "total_reach": row.total_reach or 0,
            "total_likes": row.total_likes or 0,
        }
    return results


@router.get("/content-type-performance")
async def get_content_type_performance(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Performance by content type"""
    result = await db.execute(
        select(
            ContentItem.content_type,
            func.count(ContentItem.id).label("count"),
            func.avg(ContentItem.engagement_rate).label("avg_er"),
        )
        .where(ContentItem.status == ContentStatus.PUBLISHED)
        .group_by(ContentItem.content_type)
        .order_by(desc(func.avg(ContentItem.engagement_rate)))
    )
    return [
        {
            "content_type": row.content_type.value,
            "post_count": row.count,
            "avg_engagement_rate": round(float(row.avg_er or 0), 2),
        }
        for row in result.all()
    ]


@router.post("/generate-report")
async def generate_analytics_report(current_user: User = Depends(get_current_user)):
    """Trigger AI-generated weekly analytics report"""
    from app.workers.tasks import generate_analytics_report as gen_report
    import asyncio
    result = await gen_report()
    return {"report": result, "generated": True}
