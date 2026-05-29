"""
SED Energy - WhatsApp Agent
Generates group-specific WhatsApp messages with correct tone, content, and frequency rules.
"""
import logging
import json
from anthropic import AsyncAnthropic
from app.config import settings
from app.core.prompts import WHATSAPP_AGENT_PROMPT, SED_MASTER_SYSTEM_PROMPT
from app.core.brand import SED_WHATSAPP_GROUP_PROFILES, SED_BRAND

logger = logging.getLogger("sed-ai.whatsapp-agent")

MESSAGE_TEMPLATES = {
    "stock_arrival": """\
🔆 *New Stock Arrival — {brand} {product}*

{description}

📦 Quantity: {qty} units
📍 Available: Johannesburg Warehouse

{cta}

📞 {phone} | 📧 {email}
_The SED Energy Team_""",

    "back_in_stock": """\
✅ *Back in Stock: {brand} {product}*

{description}

Limited units available — first-come, first-served.

Contact us to secure your allocation:
📞 {phone}
📧 {email}
💬 WhatsApp: {whatsapp}

_SED Energy — South Africa's Tier 1 Solar Distributor_""",

    "low_stock_alert": """\
⚡ *Low Stock Alert: {brand} {product}*

Only *{qty} units* remaining.

{cta}

📞 {phone} | 💬 {whatsapp}
_SED Energy_""",

    "educational_tip": """\
💡 *Solar Tip: {title}*

{content}

🌐 Learn more: sed.energy
_SED Energy — Your Tier 1 Solar Partner_""",

    "price_opportunity": """\
🎯 *Pricing Opportunity — {brand} {product}*

{description}

This is a *trade-only* offer. Valid while stock lasts.

To get your quote:
📞 {phone}
📧 {email}

_SED Energy Team_""",

    "general_update": """\
{content}

_The SED Energy Team_
📞 {phone} | 🌐 sed.energy""",
}


class WhatsAppAgent:
    """
    Generates targeted WhatsApp messages per group type.
    Enforces posting frequency limits and tone rules.
    """

    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    def _get_group_profile(self, group_type: str) -> dict:
        return SED_WHATSAPP_GROUP_PROFILES.get(group_type, SED_WHATSAPP_GROUP_PROFILES["installer_general"])

    def _build_group_system_prompt(self, group_type: str, group_name: str) -> str:
        profile = self._get_group_profile(group_type)
        return f"""{SED_MASTER_SYSTEM_PROMPT}

## WhatsApp Group Context
Group name: {group_name}
Group type: {group_type}
Audience: {profile['audience']}
Posting frequency: {profile['posting_frequency']}
Preferred content: {', '.join(profile['preferred_content'])}
Tone: {profile['tone']}
Avoid: {', '.join(profile['avoid'])}

## WhatsApp Formatting Rules
- Use *bold* for key info (product names, quantities, prices)
- Use line breaks generously for readability
- Keep under 200 words unless stock arrival (then up to 300)
- No excessive emojis — maximum 2-3 per message
- Always end with team sign-off
- Include contact info when relevant
- Never use markdown headers (#, ##) — they don't render in WhatsApp

## Output Format (JSON)
{{
  "message": "full WhatsApp message text",
  "message_type": "stock_arrival|educational|promotional|update",
  "urgency": "low|medium|high",
  "send_now": true/false,
  "recommended_time": "HH:MM SAST",
  "confidence_score": 0.0-1.0
}}
"""

    async def run(self, state: dict) -> dict:
        context = state.get("context", {})
        group_type = context.get("group_type", "installer_general")
        group_name = context.get("group_name", "Installer Group")
        topic = state.get("topic", "general_update")
        generated_content = state.get("generated_content", {})

        system_prompt = self._build_group_system_prompt(group_type, group_name)

        user_prompt = f"""Generate a WhatsApp message for the {group_name} group.

Topic: {topic}
Context: {json.dumps(context.get('stock_data', {}), indent=2) if context.get('stock_data') else 'N/A'}
Content brief: {generated_content.get('body', '') if generated_content else 'Generate from topic'}

Company contact info:
- Phone: {SED_BRAND['phone']}
- Email: {SED_BRAND['email']}
- WhatsApp: {SED_BRAND['whatsapp']}
"""

        try:
            response = await self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=600,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            raw = response.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1].lstrip("json").strip()

            result = json.loads(raw)
            return {
                "generated_content": {
                    **(generated_content or {}),
                    "whatsapp_message": result.get("message"),
                    "message_type": result.get("message_type"),
                    "urgency": result.get("urgency"),
                    "recommended_time": result.get("recommended_time"),
                },
                "confidence_score": float(result.get("confidence_score", 0.8)),
            }

        except Exception as e:
            logger.error(f"WhatsApp agent error: {e}", exc_info=True)
            return {
                "generated_content": generated_content,
                "error": str(e),
                "confidence_score": 0.0,
            }

    async def generate_bulk_messages(self, groups: list, topic: str, context: dict) -> list:
        """Generate tailored messages for multiple groups simultaneously"""
        messages = []
        for group in groups:
            state = {
                "topic": topic,
                "platform": "whatsapp",
                "context": {**context, "group_type": group["type"], "group_name": group["name"]},
                "generated_content": None,
            }
            result = await self.run(state)
            messages.append({
                "group_id": group["id"],
                "group_name": group["name"],
                "message": result.get("generated_content", {}).get("whatsapp_message", ""),
                "confidence_score": result.get("confidence_score", 0.0),
            })
        return messages
