"""
SED Energy - Stock Monitoring Agent
Detects inventory changes and triggers content generation workflows.
Integrates with Sage ERP and internal stock feeds.
"""
import logging
import json
import httpx
from typing import Optional
from datetime import datetime, timezone
from anthropic import AsyncAnthropic
from app.config import settings
from app.core.prompts import STOCK_AGENT_PROMPT, SED_MASTER_SYSTEM_PROMPT
from app.core.brand import SED_BRANDS_DISTRIBUTED

logger = logging.getLogger("sed-ai.stock-agent")

CONTENT_TRIGGER_MAP = {
    "new_arrival": {
        "priority": "HIGH",
        "platforms": ["whatsapp", "facebook", "instagram", "linkedin"],
        "urgency": "high",
        "content_type": "stock_arrival",
        "approval_required": True,
    },
    "back_in_stock": {
        "priority": "HIGH",
        "platforms": ["whatsapp", "facebook", "instagram"],
        "urgency": "high",
        "content_type": "stock_arrival",
        "approval_required": True,
    },
    "low_stock": {
        "priority": "MEDIUM",
        "platforms": ["whatsapp"],
        "urgency": "medium",
        "content_type": "low_stock_alert",
        "approval_required": False,
    },
    "out_of_stock": {
        "priority": "LOW",
        "platforms": ["whatsapp"],
        "urgency": "low",
        "content_type": "stock_update",
        "approval_required": False,
    },
}

BRAND_MESSAGING_TONE = {
    "Sungrow": "World's largest inverter manufacturer. Enterprise-grade reliability.",
    "Hinen": "Advanced lithium battery technology. Reliable energy storage for SA.",
    "Astronergy": "Tier 1 bankable solar panels. Field-proven in South African conditions.",
    "Hanersun": "High-efficiency monocrystalline panels. Built for performance and longevity.",
    "Sunova": "High-performance solar modules for commercial and residential applications.",
}


class StockAgent:
    """
    Monitors inventory changes and generates stock arrival content.
    """

    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def run(self, state: dict) -> dict:
        """Process a stock event and prepare context for content generation"""
        context = state.get("context", {})
        stock_event = context.get("stock_event", {})

        if not stock_event:
            logger.warning("Stock agent called with no stock event data")
            return state

        alert_type = stock_event.get("alert_type", "new_arrival")
        product = stock_event.get("product_name", "Unknown Product")
        brand = stock_event.get("brand", "Unknown Brand")
        quantity = stock_event.get("quantity", 0)

        trigger_config = CONTENT_TRIGGER_MAP.get(alert_type, CONTENT_TRIGGER_MAP["new_arrival"])
        brand_tone = BRAND_MESSAGING_TONE.get(brand, f"Premium {brand} solar equipment.")
        brand_info = SED_BRANDS_DISTRIBUTED.get(brand, {})

        # Enrich state context for content generation
        enriched_context = {
            **context,
            "stock_data": {
                "alert_type": alert_type,
                "product": product,
                "brand": brand,
                "quantity": quantity,
                "brand_description": brand_tone,
                "brand_tier": brand_info.get("tier", 1),
                "product_category": brand_info.get("category", "solar_equipment"),
                "sku": stock_event.get("sku"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "trigger_config": trigger_config,
        }

        return {
            "context": enriched_context,
            "topic": "stock_arrival",
            "content_type": trigger_config["content_type"],
            "requires_human_approval": trigger_config["approval_required"],
            "confidence_score": 0.95,  # High confidence — data-driven
        }

    async def check_sage_stock(self) -> list:
        """Poll Sage ERP for current stock levels"""
        if not settings.SAGE_API_URL or not settings.SAGE_API_KEY:
            logger.info("Sage ERP not configured, using mock data")
            return []

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{settings.SAGE_API_URL}/inventory/items",
                    headers={"Authorization": f"Bearer {settings.SAGE_API_KEY}"},
                    params={"company_id": settings.SAGE_COMPANY_ID},
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.json().get("items", [])
            except Exception as e:
                logger.error(f"Sage stock check error: {e}")
                return []

    async def analyze_stock_opportunity(self, stock_item: dict) -> dict:
        """Use AI to assess content opportunity for a stock item"""
        system_prompt = f"""{SED_MASTER_SYSTEM_PROMPT}
Analyze this stock item and assess the marketing content opportunity.
Output JSON:
{{
  "should_generate_content": true/false,
  "urgency": "low|medium|high",
  "recommended_platforms": ["platform1", "platform2"],
  "key_selling_points": ["point1", "point2"],
  "target_audience": "audience description",
  "content_angle": "suggested angle for content"
}}
"""
        response = await self.client.messages.create(
            model="claude-haiku-4-5-20251001",  # Fast model for analysis
            max_tokens=300,
            system=system_prompt,
            messages=[{"role": "user", "content": f"Stock item: {json.dumps(stock_item)}"}],
        )
        try:
            return json.loads(response.content[0].text.strip())
        except Exception:
            return {"should_generate_content": True, "urgency": "medium"}
