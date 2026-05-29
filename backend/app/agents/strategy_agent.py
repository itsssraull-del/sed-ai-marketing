"""
SED Energy - Strategy Agent
Plans content calendars and directs other agents based on context.
"""
import logging
import json
from anthropic import AsyncAnthropic
from app.config import settings
from app.core.prompts import STRATEGY_AGENT_PROMPT, SED_MASTER_SYSTEM_PROMPT
from app.core.brand import SED_CONTENT_TOPICS, PLATFORM_POSTING_GUIDELINES

logger = logging.getLogger("sed-ai.strategy-agent")

CONTENT_CALENDAR_TEMPLATE = {
    "monday":    {"platforms": ["linkedin", "facebook"],       "type": "educational",      "audience": "all"},
    "tuesday":   {"platforms": ["instagram", "facebook"],      "type": "product_showcase", "audience": "installers"},
    "wednesday": {"platforms": ["linkedin"],                   "type": "thought_leadership","audience": "epc"},
    "thursday":  {"platforms": ["facebook", "instagram"],      "type": "promotional",      "audience": "all"},
    "friday":    {"platforms": ["whatsapp", "facebook"],       "type": "stock_update",     "audience": "installers"},
    "saturday":  {"platforms": ["instagram"],                  "type": "lifestyle",        "audience": "general"},
    "sunday":    {"platforms": [],                             "type": "rest",             "audience": "none"},
}


class StrategyAgent:
    """
    Analyses context and plans optimal content strategy.
    Provides direction to Content Agent.
    """

    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def run(self, state: dict) -> dict:
        platform = state.get("platform")
        topic = state.get("topic")
        context = state.get("context", {})

        # If topic and platform are already defined, just enrich context
        if platform and topic:
            return await self._enrich_context(state)

        # Otherwise, determine optimal content strategy
        return await self._plan_content(state)

    async def _enrich_context(self, state: dict) -> dict:
        """Enrich existing task with strategic context"""
        platform = state.get("platform", "facebook")
        guidelines = PLATFORM_POSTING_GUIDELINES.get(platform, {})

        # Add strategic context to help content agent
        context = state.get("context", {})
        context["platform_guidelines"] = guidelines
        context["content_mix"] = guidelines.get("content_mix", {})

        return {"context": context}

    async def _plan_content(self, state: dict) -> dict:
        """Generate a full content strategy plan"""
        context = state.get("context", {})
        stock_summary = context.get("stock_summary", "No stock data available")
        analytics_summary = context.get("analytics_summary", "No analytics data available")
        news_summary = context.get("news_summary", "No news data available")

        system_prompt = f"""{SED_MASTER_SYSTEM_PROMPT}

You are the Strategy Agent. Given current context, decide:
1. What content topic to create next
2. Which platform to target
3. Which audience segment to address
4. What content type (image, video, text, carousel)

Output ONLY valid JSON:
{{
  "topic": "selected topic",
  "platform": "facebook|instagram|linkedin|whatsapp",
  "content_type": "image_post|video|carousel|text_post|reel",
  "target_audience": "audience segment",
  "urgency": "low|medium|high",
  "reasoning": "brief explanation",
  "posting_time": "HH:MM SAST"
}}
"""
        user_prompt = f"""Current context:
- Stock highlights: {stock_summary}
- Recent analytics: {analytics_summary}
- Industry news: {news_summary}

Decide the most valuable content to create right now for SED Energy's B2B solar audience.
"""
        try:
            response = await self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=500,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            plan = json.loads(response.content[0].text.strip())
            return {
                "platform": plan.get("platform"),
                "content_type": plan.get("content_type"),
                "topic": plan.get("topic"),
                "target_audience": plan.get("target_audience"),
                "context": {**state.get("context", {}), "strategy_plan": plan},
            }
        except Exception as e:
            logger.error(f"Strategy agent error: {e}", exc_info=True)
            # Fallback to default
            return {
                "platform": "linkedin",
                "content_type": "text_post",
                "topic": "solar_industry_education",
                "target_audience": "installers",
            }

    async def generate_weekly_calendar(self, context: dict) -> dict:
        """Generate a 7-day content calendar for all platforms"""
        system_prompt = f"""{SED_MASTER_SYSTEM_PROMPT}
Generate a 7-day content calendar for SED Energy. For each day, provide:
- Platform(s)
- Content type
- Topic
- Target audience
- Posting time (SAST)
- Brief content direction

Output as JSON array of 7 day objects.
"""
        response = await self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": f"Context: {json.dumps(context)}\n\nGenerate the weekly calendar."
            }],
        )
        return json.loads(response.content[0].text.strip())
