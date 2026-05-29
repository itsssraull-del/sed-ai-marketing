"""
SED Energy - Analytics Agent
Fetches engagement data, identifies top performers, generates insights, drives learning loop.
"""
import logging
import json
import httpx
from datetime import datetime, timezone, timedelta
from anthropic import AsyncAnthropic
from app.config import settings
from app.core.prompts import ANALYTICS_AGENT_PROMPT, SED_MASTER_SYSTEM_PROMPT

logger = logging.getLogger("sed-ai.analytics-agent")


class AnalyticsAgent:
    """
    Fetches platform analytics, scores content performance, generates insights.
    """

    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def run(self, state: dict) -> dict:
        context = state.get("context", {})
        report_type = context.get("report_type", "weekly_summary")

        if report_type == "weekly_summary":
            return await self._generate_weekly_report(state)
        elif report_type == "post_performance":
            return await self._analyze_post(state)
        return state

    async def fetch_facebook_insights(self, post_ids: list) -> list:
        """Fetch Facebook/Instagram insights via Meta Graph API"""
        if not settings.META_ACCESS_TOKEN:
            return []

        results = []
        async with httpx.AsyncClient() as client:
            for post_id in post_ids:
                try:
                    response = await client.get(
                        f"https://graph.facebook.com/{settings.META_GRAPH_API_VERSION}/{post_id}/insights",
                        params={
                            "metric": "post_impressions,post_reach,post_engaged_users,post_reactions_by_type_total",
                            "access_token": settings.META_ACCESS_TOKEN,
                        },
                        timeout=15.0,
                    )
                    if response.status_code == 200:
                        data = response.json()
                        results.append({"post_id": post_id, "insights": data.get("data", [])})
                except Exception as e:
                    logger.error(f"Facebook insights error for {post_id}: {e}")
        return results

    async def fetch_linkedin_analytics(self, post_urns: list) -> list:
        """Fetch LinkedIn post analytics"""
        if not settings.LINKEDIN_ACCESS_TOKEN:
            return []

        results = []
        async with httpx.AsyncClient() as client:
            for urn in post_urns:
                try:
                    response = await client.get(
                        f"https://api.linkedin.com/v2/socialActions/{urn}",
                        headers={"Authorization": f"Bearer {settings.LINKEDIN_ACCESS_TOKEN}"},
                        timeout=15.0,
                    )
                    if response.status_code == 200:
                        results.append({"urn": urn, "data": response.json()})
                except Exception as e:
                    logger.error(f"LinkedIn analytics error for {urn}: {e}")
        return results

    def calculate_engagement_rate(self, likes: int, comments: int, shares: int, reach: int) -> float:
        if reach == 0:
            return 0.0
        total_engagement = likes + (comments * 2) + (shares * 3)  # Weighted
        return round((total_engagement / reach) * 100, 2)

    def score_performance(self, engagement_rate: float, platform: str) -> str:
        benchmarks = {
            "facebook": {"high": 3.0, "medium": 1.5},
            "instagram": {"high": 4.0, "medium": 2.0},
            "linkedin": {"high": 2.5, "medium": 1.0},
        }
        bench = benchmarks.get(platform, {"high": 3.0, "medium": 1.5})
        if engagement_rate >= bench["high"]:
            return "high"
        elif engagement_rate >= bench["medium"]:
            return "medium"
        return "low"

    async def _generate_weekly_report(self, state: dict) -> dict:
        context = state.get("context", {})
        analytics_data = context.get("analytics_data", {})

        system_prompt = f"""{SED_MASTER_SYSTEM_PROMPT}

You are the Analytics Agent. Generate a weekly performance report and actionable insights.

Output JSON:
{{
  "report_period": "date range",
  "top_performing_content": [
    {{"title": "...", "platform": "...", "engagement_rate": 0.0, "why_it_worked": "..."}}
  ],
  "underperforming_content": [...],
  "platform_summary": {{
    "facebook": {{"avg_engagement": 0.0, "total_reach": 0, "best_content_type": "..."}},
    "instagram": {{}},
    "linkedin": {{}}
  }},
  "key_insights": ["insight1", "insight2"],
  "recommendations": ["action1", "action2"],
  "next_week_focus": ["priority1", "priority2"]
}}
"""
        try:
            response = await self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1500,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"Analytics data from last 7 days:\n{json.dumps(analytics_data, indent=2)}"
                }],
            )
            raw = response.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1].lstrip("json").strip()
            report = json.loads(raw)
            return {
                "final_output": {"report": report, "type": "weekly_analytics"},
                "context": {**context, "analytics_report": report},
            }
        except Exception as e:
            logger.error(f"Analytics report error: {e}")
            return state

    async def _analyze_post(self, state: dict) -> dict:
        context = state.get("context", {})
        post_data = context.get("post_data", {})
        er = self.calculate_engagement_rate(
            post_data.get("likes", 0),
            post_data.get("comments", 0),
            post_data.get("shares", 0),
            post_data.get("reach", 1),
        )
        score = self.score_performance(er, post_data.get("platform", "facebook"))
        return {
            "context": {
                **context,
                "performance": {"engagement_rate": er, "score": score},
            }
        }
