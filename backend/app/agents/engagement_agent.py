"""
SED Energy - Engagement Agent
Monitors comments, generates reply suggestions, manages community interactions.
"""
import logging
import json
from anthropic import AsyncAnthropic
from app.config import settings
from app.core.prompts import SED_MASTER_SYSTEM_PROMPT

logger = logging.getLogger("sed-ai.engagement-agent")

ENGAGEMENT_CATEGORIES = {
    "inquiry": "Customer asking about products/pricing/availability",
    "positive_feedback": "Compliment or positive reaction",
    "negative_feedback": "Complaint or negative reaction",
    "technical_question": "Technical solar question",
    "quote_request": "Requesting a quote",
    "spam": "Irrelevant or spam comment",
    "competitor_mention": "Mentions a competitor",
}

AUTO_REPLY_ELIGIBLE = ["positive_feedback", "technical_question"]
HUMAN_REQUIRED = ["negative_feedback", "quote_request", "competitor_mention"]


class EngagementAgent:
    """
    Generates reply suggestions for social media comments and DMs.
    Routes complex queries to human team.
    """

    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def run(self, state: dict) -> dict:
        context = state.get("context", {})
        comments = context.get("comments", [])
        if not comments:
            return state

        replies = []
        for comment in comments[:20]:  # Process up to 20 at a time
            reply = await self.generate_reply(comment)
            replies.append(reply)

        return {
            "final_output": {"replies": replies, "type": "engagement_replies"},
            "context": {**context, "generated_replies": replies},
        }

    async def generate_reply(self, comment: dict) -> dict:
        platform = comment.get("platform", "facebook")
        text = comment.get("text", "")
        author = comment.get("author_name", "there")

        category = await self.categorize_comment(text)
        requires_human = category in HUMAN_REQUIRED

        if requires_human:
            return {
                "comment_id": comment.get("id"),
                "category": category,
                "requires_human": True,
                "suggested_reply": None,
                "alert_message": f"Human review required: {category} from {author}",
            }

        system_prompt = f"""{SED_MASTER_SYSTEM_PROMPT}

You are managing SED Energy's {platform} community.
Reply to this comment professionally and helpfully.

Rules:
- Keep replies concise (1-3 sentences for most cases)
- Be warm and professional — we are a B2B partner, not a transactional retailer
- For technical questions: give a helpful answer and offer to connect via phone/email
- For positive feedback: acknowledge warmly, reinforce brand value
- Never mention competitor products
- Always sign off as "SED Energy" or "The SED Team"
- For quote requests, direct to: info@sed.energy or 010 006 8246

Return ONLY the reply text.
"""

        try:
            response = await self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=200,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"Comment from {author}: {text}"
                }],
            )
            reply_text = response.content[0].text.strip()
            return {
                "comment_id": comment.get("id"),
                "category": category,
                "requires_human": False,
                "suggested_reply": reply_text,
                "auto_post": category in AUTO_REPLY_ELIGIBLE,
            }
        except Exception as e:
            logger.error(f"Engagement reply error: {e}")
            return {
                "comment_id": comment.get("id"),
                "requires_human": True,
                "error": str(e),
            }

    async def categorize_comment(self, text: str) -> str:
        """Quick categorization using fast model"""
        categories = list(ENGAGEMENT_CATEGORIES.keys())
        try:
            response = await self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=20,
                system=f"Categorize this comment as one of: {', '.join(categories)}. Return ONLY the category name.",
                messages=[{"role": "user", "content": text}],
            )
            category = response.content[0].text.strip().lower()
            return category if category in categories else "inquiry"
        except Exception:
            return "inquiry"
