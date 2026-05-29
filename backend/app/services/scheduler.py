"""
SED Energy - Content Scheduler Service
Manages scheduled post publishing via APScheduler + Redis.
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor

logger = logging.getLogger("sed-ai.scheduler")


def build_scheduler(redis_url: str) -> AsyncIOScheduler:
    """Build and return a configured APScheduler instance"""
    jobstores = {
        "default": RedisJobStore(jobs_key="sed:jobs", run_times_key="sed:run_times", url=redis_url)
    }
    executors = {"default": AsyncIOExecutor()}
    job_defaults = {"coalesce": False, "max_instances": 3, "misfire_grace_time": 300}

    scheduler = AsyncIOScheduler(
        jobstores=jobstores,
        executors=executors,
        job_defaults=job_defaults,
        timezone="Africa/Johannesburg",
    )
    return scheduler


class SchedulerService:
    """
    Manages content scheduling, cron jobs for analytics, stock polling,
    and news monitoring.
    """

    def __init__(self, redis_url: str):
        self.scheduler = build_scheduler(redis_url)

    def start(self):
        """Start scheduler and register all system cron jobs"""
        self.scheduler.start()
        self._register_system_jobs()
        logger.info("✅ Scheduler started with system jobs registered")

    def stop(self):
        self.scheduler.shutdown(wait=False)

    def _register_system_jobs(self):
        """Register all background system jobs"""
        # Publish scheduled content every 5 minutes
        self.scheduler.add_job(
            self._job_publish_due_posts,
            "interval", minutes=5, id="publish_due_posts", replace_existing=True,
        )
        # Fetch analytics for published posts daily at 08:00 SAST
        self.scheduler.add_job(
            self._job_fetch_analytics,
            "cron", hour=8, minute=0, id="fetch_analytics", replace_existing=True,
        )
        # Check stock (Sage poll) every 30 minutes during business hours
        self.scheduler.add_job(
            self._job_check_stock,
            "cron", hour="7-18", minute="*/30", id="check_stock", replace_existing=True,
        )
        # Monitor news feeds twice daily
        self.scheduler.add_job(
            self._job_monitor_news,
            "cron", hour="7,13", minute=0, id="monitor_news", replace_existing=True,
        )
        # Generate weekly content calendar every Sunday at 18:00
        self.scheduler.add_job(
            self._job_generate_weekly_calendar,
            "cron", day_of_week="sun", hour=18, id="weekly_calendar", replace_existing=True,
        )
        # Analytics weekly report every Monday at 07:00
        self.scheduler.add_job(
            self._job_weekly_analytics_report,
            "cron", day_of_week="mon", hour=7, id="weekly_report", replace_existing=True,
        )

    async def _job_publish_due_posts(self):
        """Find and publish all scheduled posts that are due"""
        from app.workers.tasks import publish_scheduled_posts
        await publish_scheduled_posts()

    async def _job_fetch_analytics(self):
        from app.workers.tasks import fetch_platform_analytics
        await fetch_platform_analytics()

    async def _job_check_stock(self):
        from app.workers.tasks import check_stock_updates
        await check_stock_updates()

    async def _job_monitor_news(self):
        from app.workers.tasks import monitor_industry_news
        await monitor_industry_news()

    async def _job_generate_weekly_calendar(self):
        from app.workers.tasks import generate_weekly_content_calendar
        await generate_weekly_content_calendar()

    async def _job_weekly_analytics_report(self):
        from app.workers.tasks import generate_analytics_report
        await generate_analytics_report()

    def schedule_post(self, content_item_id: str, scheduled_for: datetime, platform: str) -> str:
        """Schedule a specific content item for publishing"""
        job_id = f"post_{content_item_id}_{platform}"
        self.scheduler.add_job(
            self._publish_single_post,
            "date",
            run_date=scheduled_for,
            args=[content_item_id, platform],
            id=job_id,
            replace_existing=True,
        )
        logger.info(f"Scheduled post {content_item_id} for {scheduled_for} on {platform}")
        return job_id

    async def _publish_single_post(self, content_item_id: str, platform: str):
        from app.workers.tasks import publish_single_post
        await publish_single_post(content_item_id, platform)

    def list_scheduled_jobs(self) -> list:
        return [
            {
                "id": job.id,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
            }
            for job in self.scheduler.get_jobs()
        ]


_scheduler: Optional[SchedulerService] = None


def get_scheduler(redis_url: str = None) -> SchedulerService:
    global _scheduler
    if _scheduler is None:
        from app.config import settings
        _scheduler = SchedulerService(redis_url or settings.REDIS_URL)
    return _scheduler
