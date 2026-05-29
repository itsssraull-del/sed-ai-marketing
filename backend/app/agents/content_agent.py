"""
SED Energy - Content Generation Agent
Generates platform-optimised, brand-accurate content using Claude API + RAG context
"""
import logging
import json
from typing import Optional
from anthropic import AsyncAnthropic
from app.config import settings
from app.core.prompts import CONTENT_AGENT_PROMPT, SED_MASTER_SYSTEM_PROMPT
from app.core.brand import PLATFORM_POSTING_GUIDELINES, SED_BRAND

logger = logging.getLogger("sed-ai.content-agent")

PLATFORM_INSTRUCTIONS = {
    "facebook": {
        "format": "Write an engaging Facebook post. Include a hook, value, and call to action.",
        "max_length": 400,
        "hashtag_count": "8-12",
    },
    "instagram": {
        "format": "Write an Instagram caption: punchy first line, value-packed body, strong CTA. Hashtags in first comment.",
        "max_length": 300,
        "hashtag_count": "20-30",
    },
    "linkedin": {
        "format": "Write a professional LinkedIn post. Lead with insight, build credibility, include data when available.",
        "max_length": 600,
        "hashtag_count": "3-5",
    },
    "whatsapp": {
        "format": "Write a concise, scannable WhatsApp message. Use *bold* for key points. No excessive formatting.",
        "max_length": 300,
        "hashtag_count": "0",
    },
}

CONTENT_TYPE_TEMPLATES = {
    "stock_arrival": {
        "hook": "New {brand} {product} stock has landed at our Johannesburg warehouse.",
        "urgency": "medium",
        "include_cta": True,
    },
    "educational": {
        "hook": "Here's what every solar professional needs to know about {topic}.",
        "urgency": "low",
        "include_cta": False,
    },
    "promotional": {
        "hook": "Limited availability — {product} at competitive wholesale pricing.",
        "urgency": "high",
        "include_cta": True,
    },
    "industry_news": {
        "hook": "Industry update: {headline}",
        "urgency": "medium",
        "include_cta": False,
    },
    "thought_leadership": {
        "hook": "The South African solar market is shifting. Here's what that means for installers.",
        "urgency": "low",
        "include_cta": False,
    },
}


class ContentAgent:
    """
    Generates platform-specific, brand-accurate content for SED Energy.
    Uses Claude API with RAG context injection.
    """

    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-opus-4-6"

    def _build_system_prompt(self, platform: str, content_type: str) -> str:
        platform_guide = PLATFORM_POSTING_GUIDELINES.get(platform, {})
        platform_instr = PLATFORM_INSTRUCTIONS.get(platform, {})

        return f"""{SED_MASTER_SYSTEM_PROMPT}

## Your Role in This Request
You are generating {content_type} content for {platform.upper()}.

## Platform-Specific Instructions
{platform_instr.get('format', '')}
Maximum length: {platform_instr.get('max_length', 400)} words
Hashtag count: {platform_instr.get('hashtag_count', '5-10')}

## Best Posting Times (SAST)
{', '.join(platform_guide.get('best_times_sast', []))}

## Output Format (JSON)
Return ONLY valid JSON with this structure:
{{
  "title": "Internal content title",
  "body": "Main post content",
  "hashtags": ["hashtag1", "hashtag2"],
  "image_description": "Brief description of ideal image for this post",
  "cta": "Call to action text",
  "posting_time_recommendation": "HH:MM SAST",
  "confidence_score": 0.0-1.0,
  "requires_approval": true/false,
  "approval_reason": "Reason if requires_approval is true",
  "content_type": "{content_type}",
  "platform": "{platform}",
  "has_pricing": false,
  "has_specs": false
}}
"""

    def _build_user_prompt(self, state: dict) -> str:
        topic = state.get("topic", "solar energy")
        target_audience = state.get("target_audience", "solar installers")
        context = state.get("context", {})
        platform = state.get("platform", "facebook")
        content_type = state.get("content_type", "educational")

        rag_context = context.get("rag_context", "")
        stock_context = context.get("stock_data", "")
        news_context = context.get("news_data", "")

        prompt = f"""Generate a {content_type} post for {platform} targeting {target_audience}.

Topic: {topic}
"""
        if rag_context:
            prompt += f"\n## Verified Knowledge Base Context\n{rag_context}\n"
        if stock_context:
            prompt += f"\n## Current Stock Data (VERIFIED)\n{stock_context}\n"
        if news_context:
            prompt += f"\n## Industry News Context\n{news_context}\n"

        prompt += """
IMPORTANT:
- Only reference products and brands confirmed in the knowledge base context
- Do not invent specifications, pricing, or warranty details
- If unsure about any fact, set confidence_score below 0.8 and requires_approval to true
- Output ONLY the JSON object, no other text
"""
        return prompt

    async def run(self, state: dict) -> dict:
        platform = state.get("platform", "facebook")
        content_type = state.get("content_type", "educational")

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                system=self._build_system_prompt(platform, content_type),
                messages=[{"role": "user", "content": self._build_user_prompt(state)}],
            )

            raw_content = response.content[0].text.strip()

            # Parse JSON response
            try:
                # Handle potential markdown code blocks
                if raw_content.startswith("```"):
                    raw_content = raw_content.split("```")[1]
                    if raw_content.startswith("json"):
                        raw_content = raw_content[4:]
                content_data = json.loads(raw_content)
            except json.JSONDecodeError:
                logger.warning("Content agent returned non-JSON, wrapping...")
                content_data = {
                    "body": raw_content,
                    "confidence_score": 0.6,
                    "requires_approval": True,
                    "platform": platform,
                    "content_type": content_type,
                }

            return {
                "generated_content": content_data,
                "confidence_score": float(content_data.get("confidence_score", 0.7)),
                "requires_human_approval": content_data.get("requires_approval", True),
            }

        except Exception as e:
            logger.error(f"Content agent error: {e}", exc_info=True)
            return {
                "generated_content": None,
                "error": str(e),
                "confidence_score": 0.0,
                "requires_human_approval": True,
            }
