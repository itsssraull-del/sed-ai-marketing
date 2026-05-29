"""
SED Energy - Celery Worker Configuration
Heavy async tasks: image generation, video generation, batch content creation
"""
from celery import Celery
from app.config import settings

celery_app = Celery(
    "sed-marketing",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Africa/Johannesburg",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,  # Process one task at a time per worker
    task_routes={
        "app.workers.tasks.generate_image_task": {"queue": "image_gen"},
        "app.workers.tasks.generate_video_task": {"queue": "video_gen"},
        "app.workers.tasks.ingest_document_task": {"queue": "ingestion"},
        "app.workers.tasks.generate_content_batch": {"queue": "content"},
        "app.workers.tasks.publish_post_task": {"queue": "publishing"},
    },
    beat_schedule={
        "publish-due-posts": {
            "task": "app.workers.tasks.publish_scheduled_posts_task",
            "schedule": 300.0,  # Every 5 minutes
        },
        "check-stock-updates": {
            "task": "app.workers.tasks.check_stock_updates_task",
            "schedule": 1800.0,  # Every 30 minutes
        },
        "fetch-analytics": {
            "task": "app.workers.tasks.fetch_platform_analytics_task",
            "schedule": 86400.0,  # Daily
        },
        "monitor-news": {
            "task": "app.workers.tasks.monitor_industry_news_task",
            "schedule": 21600.0,  # Every 6 hours
        },
    },
)
