"""System settings and scheduler management routes"""
from fastapi import APIRouter, Depends
from app.models.user import User
from app.core.security import get_current_user, require_admin
from app.services.scheduler import get_scheduler

router = APIRouter()


@router.get("/scheduler/jobs", dependencies=[Depends(require_admin)])
async def list_scheduler_jobs():
    """List all registered scheduler jobs"""
    scheduler = get_scheduler()
    return {"jobs": scheduler.list_scheduled_jobs()}


@router.post("/scheduler/trigger/{job_name}", dependencies=[Depends(require_admin)])
async def trigger_job(job_name: str):
    """Manually trigger a specific background job"""
    from app.workers.tasks import (
        publish_scheduled_posts, check_stock_updates,
        fetch_platform_analytics, monitor_industry_news,
        generate_weekly_content_calendar, generate_analytics_report
    )
    job_map = {
        "publish_posts": publish_scheduled_posts,
        "check_stock": check_stock_updates,
        "fetch_analytics": fetch_platform_analytics,
        "monitor_news": monitor_industry_news,
        "weekly_calendar": generate_weekly_content_calendar,
        "analytics_report": generate_analytics_report,
    }
    if job_name not in job_map:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Job '{job_name}' not found. Options: {list(job_map.keys())}")

    result = await job_map[job_name]()
    return {"job": job_name, "status": "completed", "result": str(result)[:500]}


@router.get("/brand-config")
async def get_brand_config(current_user: User = Depends(get_current_user)):
    """Get SED brand configuration (read-only)"""
    from app.core.brand import SED_BRAND, SED_BRANDS_DISTRIBUTED, PLATFORM_POSTING_GUIDELINES
    return {
        "brand": SED_BRAND,
        "distributed_brands": SED_BRANDS_DISTRIBUTED,
        "platform_guidelines": PLATFORM_POSTING_GUIDELINES,
    }


@router.get("/health/services")
async def check_service_health(current_user: User = Depends(require_admin)):
    """Check connectivity status of all external services"""
    import httpx
    from app.config import settings

    statuses = {}

    # Check Pinecone
    try:
        from app.services.vector_store import get_vector_store
        vs = get_vector_store()
        stats = await vs.get_stats()
        statuses["pinecone"] = {"status": "ok", "vectors": stats.get("total_vectors", 0)}
    except Exception as e:
        statuses["pinecone"] = {"status": "error", "error": str(e)}

    # Check Meta Graph API
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"https://graph.facebook.com/{settings.META_GRAPH_API_VERSION}/me",
                params={"access_token": settings.META_ACCESS_TOKEN},
                timeout=10.0,
            )
            statuses["meta_graph"] = {"status": "ok" if r.status_code == 200 else "error"}
    except Exception as e:
        statuses["meta_graph"] = {"status": "error", "error": str(e)}

    # Check LinkedIn
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                "https://api.linkedin.com/v2/me",
                headers={"Authorization": f"Bearer {settings.LINKEDIN_ACCESS_TOKEN}"},
                timeout=10.0,
            )
            statuses["linkedin"] = {"status": "ok" if r.status_code == 200 else "error"}
    except Exception as e:
        statuses["linkedin"] = {"status": "error", "error": str(e)}

    # Check Sage
    if settings.SAGE_API_URL:
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(settings.SAGE_API_URL, timeout=10.0)
                statuses["sage_erp"] = {"status": "ok" if r.status_code < 500 else "error"}
        except Exception as e:
            statuses["sage_erp"] = {"status": "error", "error": str(e)}
    else:
        statuses["sage_erp"] = {"status": "not_configured"}

    return {"services": statuses}
