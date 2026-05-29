"""
SED Energy - Celery Tasks
All background task definitions.
"""
import logging
import asyncio
from datetime import datetime, timezone
from app.workers.celery_app import celery_app

logger = logging.getLogger("sed-ai.tasks")


def run_async(coro):
    """Helper to run async code in Celery tasks"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ─── Image Generation ────────────────────────────────────────────────────────

@celery_app.task(bind=True, name="app.workers.tasks.generate_image_task", max_retries=2)
def generate_image_task(self, prompt: str, platform: str, content_type: str,
                         content_item_id: str, provider: str = "flux"):
    """Generate an image and attach it to a content item"""
    try:
        from app.services.image_generation import ImageGenerationService
        from app.database import AsyncSessionLocal
        from app.models.content import ContentItem
        from sqlalchemy import select

        service = ImageGenerationService()
        image_url = run_async(service.generate(prompt, platform, content_type, provider))

        if image_url:
            async def update_db():
                async with AsyncSessionLocal() as db:
                    result = await db.execute(select(ContentItem).where(ContentItem.id == content_item_id))
                    item = result.scalar_one_or_none()
                    if item:
                        item.image_url = image_url
                        await db.commit()
            run_async(update_db())
            logger.info(f"Image generated and saved for content {content_item_id}: {image_url}")
            return {"success": True, "image_url": image_url}
        return {"success": False, "error": "Image generation returned no URL"}

    except Exception as exc:
        logger.error(f"Image generation task failed: {exc}")
        raise self.retry(exc=exc, countdown=30)


# ─── Video Generation ────────────────────────────────────────────────────────

@celery_app.task(bind=True, name="app.workers.tasks.generate_video_task", max_retries=1)
def generate_video_task(self, prompt: str, platform: str, content_item_id: str,
                         image_url: str = None):
    """Generate a video via Runway ML and attach to content item"""
    try:
        from app.agents.video_agent import VideoAgent
        agent = VideoAgent()
        result = run_async(agent.trigger_runway_generation(prompt, image_url))
        logger.info(f"Video generation triggered for {content_item_id}: {result}")
        return {"success": True, "runway_response": result}
    except Exception as exc:
        logger.error(f"Video task failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


# ─── Document Ingestion ──────────────────────────────────────────────────────

@celery_app.task(bind=True, name="app.workers.tasks.ingest_document_task", max_retries=2)
def ingest_document_task(self, s3_key: str, document_type: str, document_id: str):
    """Ingest a document from S3 into the vector knowledge base"""
    try:
        from app.services.nas_ingestion import NASIngestionService
        service = NASIngestionService()
        result = run_async(service.ingest_from_s3(s3_key, document_type, document_id))
        logger.info(f"Document ingested: {document_id} — {result.get('chunks', 0)} chunks")
        return result
    except Exception as exc:
        logger.error(f"Ingestion task failed for {document_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


# ─── Content Generation ──────────────────────────────────────────────────────

@celery_app.task(name="app.workers.tasks.generate_content_batch")
def generate_content_batch(platform: str, content_type: str, topic: str,
                            target_audience: str = "installers"):
    """Generate a batch of content items for a platform"""
    from app.agents.orchestrator import get_orchestrator
    orchestrator = get_orchestrator()
    result = run_async(orchestrator.run(
        task_type="generate_content",
        platform=platform,
        content_type=content_type,
        topic=topic,
        target_audience=target_audience,
    ))
    logger.info(f"Content batch generated: {platform}/{content_type}/{topic}")
    return result


# ─── Publishing ──────────────────────────────────────────────────────────────

@celery_app.task(name="app.workers.tasks.publish_post_task")
def publish_post_task(content_item_id: str):
    """Publish a specific content item to its target platform"""
    return run_async(_publish_content_item(content_item_id))


async def _publish_content_item(content_item_id: str):
    from app.services.social_publisher import SocialPublisherService
    from app.database import AsyncSessionLocal
    from app.models.content import ContentItem, ContentStatus
    from sqlalchemy import select

    publisher = SocialPublisherService()
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(ContentItem).where(ContentItem.id == content_item_id))
        item = result.scalar_one_or_none()
        if not item or item.status != ContentStatus.APPROVED:
            return {"error": "Content not found or not approved"}

        publish_result = await publisher.publish({
            "platform": item.platform.value,
            "body": item.body,
            "caption": item.caption,
            "image_url": item.image_url,
            "video_url": item.video_url,
            "content_type": item.content_type.value,
        })

        if publish_result.get("success"):
            item.status = ContentStatus.PUBLISHED
            item.platform_post_id = publish_result.get("post_id")
            item.published_at = datetime.now(timezone.utc).isoformat()
        else:
            item.status = ContentStatus.FAILED

        await db.commit()
        return publish_result


# ─── System Jobs (called by beat scheduler) ──────────────────────────────────

@celery_app.task(name="app.workers.tasks.publish_scheduled_posts_task")
def publish_scheduled_posts_task():
    return run_async(publish_scheduled_posts())


@celery_app.task(name="app.workers.tasks.check_stock_updates_task")
def check_stock_updates_task():
    return run_async(check_stock_updates())


@celery_app.task(name="app.workers.tasks.fetch_platform_analytics_task")
def fetch_platform_analytics_task():
    return run_async(fetch_platform_analytics())


@celery_app.task(name="app.workers.tasks.monitor_industry_news_task")
def monitor_industry_news_task():
    return run_async(monitor_industry_news())


async def publish_scheduled_posts():
    """Find all due scheduled posts and publish them"""
    from app.database import AsyncSessionLocal
    from app.models.content import ContentItem, ContentStatus
    from sqlalchemy import select, and_
    now = datetime.now(timezone.utc).isoformat()

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ContentItem).where(
                and_(
                    ContentItem.status == ContentStatus.APPROVED,
                    ContentItem.scheduled_for <= now,
                )
            )
        )
        items = result.scalars().all()

    for item in items:
        publish_post_task.delay(str(item.id))
    logger.info(f"Triggered publishing for {len(items)} due posts")


async def check_stock_updates():
    """Poll stock sources and trigger content for any changes"""
    from app.agents.stock_agent import StockAgent
    from app.agents.orchestrator import get_orchestrator

    agent = StockAgent()
    stock_items = await agent.check_sage_stock()

    for item in stock_items:
        opportunity = await agent.analyze_stock_opportunity(item)
        if opportunity.get("should_generate_content"):
            orchestrator = get_orchestrator()
            await orchestrator.run(
                task_type="stock_alert",
                context={"stock_event": {**item, "alert_type": "new_arrival"}},
            )


async def fetch_platform_analytics():
    """Fetch and store analytics for all recently published posts"""
    from app.agents.analytics_agent import AnalyticsAgent
    from app.database import AsyncSessionLocal
    from app.models.content import ContentItem, ContentStatus
    from sqlalchemy import select
    from datetime import timedelta

    analytics = AnalyticsAgent()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ContentItem).where(
                ContentItem.status == ContentStatus.PUBLISHED,
                ContentItem.published_at >= cutoff,
                ContentItem.platform_post_id.isnot(None),
            )
        )
        items = result.scalars().all()

    facebook_ids = [i.platform_post_id for i in items if i.platform.value == "facebook"]
    if facebook_ids:
        await analytics.fetch_facebook_insights(facebook_ids[:50])

    logger.info(f"Analytics fetched for {len(items)} posts")


async def monitor_industry_news():
    """Check for relevant industry news and generate content opportunities"""
    from app.agents.news_agent import NewsAgent
    from app.agents.orchestrator import get_orchestrator

    news_agent = NewsAgent()
    opportunities = await news_agent.analyze_opportunities(await news_agent.fetch_news())
    high_priority = [o for o in opportunities if o.get("urgency") == "high"]

    for opp in high_priority[:2]:  # Max 2 news-driven posts per run
        orchestrator = get_orchestrator()
        await orchestrator.run(
            task_type="news_response",
            platform=opp.get("platforms", ["facebook"])[0],
            topic=opp.get("content_angle", "industry_news"),
            context={"news_data": opp},
        )


async def generate_weekly_content_calendar():
    from app.agents.strategy_agent import StrategyAgent
    agent = StrategyAgent()
    calendar = await agent.generate_weekly_calendar({})
    logger.info("Weekly content calendar generated")
    return calendar


async def generate_analytics_report():
    from app.agents.analytics_agent import AnalyticsAgent
    agent = AnalyticsAgent()
    result = await agent.run({"context": {"report_type": "weekly_summary", "analytics_data": {}}})
    logger.info("Weekly analytics report generated")
    return result


async def publish_single_post(content_item_id: str, platform: str):
    return await _publish_content_item(content_item_id)
