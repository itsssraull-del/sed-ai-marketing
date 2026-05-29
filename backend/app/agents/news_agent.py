"""
SED Energy - Industry News Agent
Monitors SA solar industry news, Eskom updates, and market trends.
Identifies content opportunities and triggers relevant posts.
"""
import logging
import json
import httpx
from datetime import datetime, timezone, timedelta
from anthropic import AsyncAnthropic
from app.config import settings
from app.core.prompts import NEWS_AGENT_PROMPT, SED_MASTER_SYSTEM_PROMPT

logger = logging.getLogger("sed-ai.news-agent")

NEWS_SEARCH_QUERIES = [
    "South Africa solar energy",
    "Eskom load shedding schedule",
    "NERSA solar regulation South Africa",
    "South Africa renewable energy",
    "solar panel price South Africa",
    "loadshedding stage update",
    "South Africa energy market",
    "C&I solar South Africa",
    "Sungrow Astronergy solar news",
]

CONTENT_OPPORTUNITY_TRIGGERS = {
    "loadshedding_increase": {
        "urgency": "high",
        "platforms": ["facebook", "whatsapp", "instagram"],
        "content_type": "urgency_post",
    },
    "loadshedding_decrease": {
        "urgency": "medium",
        "platforms": ["linkedin", "facebook"],
        "content_type": "educational",
    },
    "nersa_regulation": {
        "urgency": "medium",
        "platforms": ["linkedin", "facebook"],
        "content_type": "regulatory_update",
    },
    "solar_price_drop": {
        "urgency": "high",
        "platforms": ["facebook", "whatsapp", "linkedin"],
        "content_type": "market_update",
    },
    "technology_breakthrough": {
        "urgency": "low",
        "platforms": ["linkedin", "facebook", "instagram"],
        "content_type": "educational",
    },
}


class NewsAgent:
    """
    Fetches and analyses SA solar industry news, identifies content opportunities.
    """

    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def run(self, state: dict) -> dict:
        news_items = await self.fetch_news()
        if not news_items:
            return state

        opportunities = await self.analyze_opportunities(news_items)
        if not opportunities:
            return state

        # Pick the highest-value opportunity
        top_opportunity = opportunities[0]
        context = state.get("context", {})

        return {
            "context": {
                **context,
                "news_data": top_opportunity,
                "all_news_opportunities": opportunities[:3],
            },
            "topic": top_opportunity.get("content_angle", "industry_news"),
            "content_type": top_opportunity.get("content_type", "educational"),
        }

    async def fetch_news(self) -> list:
        """Fetch solar industry news from NewsAPI"""
        if not settings.NEWS_API_KEY:
            logger.info("NewsAPI key not configured, returning empty news")
            return []

        articles = []
        async with httpx.AsyncClient() as client:
            for query in NEWS_SEARCH_QUERIES[:3]:  # Limit to 3 queries per run
                try:
                    response = await client.get(
                        "https://newsapi.org/v2/everything",
                        params={
                            "q": query,
                            "language": "en",
                            "sortBy": "publishedAt",
                            "from": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
                            "pageSize": 5,
                            "apiKey": settings.NEWS_API_KEY,
                        },
                        timeout=15.0,
                    )
                    if response.status_code == 200:
                        articles.extend(response.json().get("articles", []))
                except Exception as e:
                    logger.error(f"News fetch error for '{query}': {e}")

        return articles

    async def analyze_opportunities(self, articles: list) -> list:
        """Use Claude to analyze news articles for content opportunities"""
        if not articles:
            return []

        article_summaries = "\n".join([
            f"- {a.get('title', '')} ({a.get('source', {}).get('name', '')})"
            for a in articles[:10]
        ])

        system_prompt = f"""{SED_MASTER_SYSTEM_PROMPT}

Analyze these solar industry news headlines for marketing content opportunities for SED Energy.

For each relevant opportunity, output:
{{
  "headline": "relevant headline",
  "source": "news source",
  "relevance_score": 0.0-1.0,
  "opportunity_type": "loadshedding_increase|nersa_regulation|market_update|educational|general",
  "content_angle": "how SED should frame this",
  "content_type": "educational|urgency_post|market_update|thought_leadership",
  "platforms": ["facebook", "linkedin"],
  "urgency": "low|medium|high",
  "talking_points": ["point1", "point2"]
}}

Return a JSON array of opportunities sorted by relevance_score descending.
Only include items with relevance_score >= 0.6.
"""
        try:
            response = await self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1000,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"News headlines:\n{article_summaries}"
                }],
            )
            raw = response.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1].lstrip("json").strip()
            return json.loads(raw)
        except Exception as e:
            logger.error(f"News analysis error: {e}")
            return []

    async def get_eskom_status(self) -> dict:
        """Fetch current Eskom load-shedding stage"""
        try:
            async with httpx.AsyncClient() as client:
                # EskomSePush API
                response = await client.get(
                    "https://developer.sepush.co.za/business/2.0/status",
                    headers={"Token": settings.NEWS_API_KEY or ""},
                    timeout=10.0,
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.debug(f"Eskom status check failed: {e}")
        return {"status": "unknown"}
