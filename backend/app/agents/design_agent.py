"""
SED Energy - Design Agent
Generates precise image prompts for AI image generation (Flux via Replicate, SDXL, DALL-E 3).
"""
import logging
import json
from anthropic import AsyncAnthropic
from app.config import settings
from app.core.prompts import DESIGN_AGENT_PROMPT, SED_MASTER_SYSTEM_PROMPT
from app.core.brand import SED_BRAND

logger = logging.getLogger("sed-ai.design-agent")

# Aspect ratios per platform/content type
ASPECT_RATIOS = {
    "instagram_feed": "1:1",
    "instagram_story": "9:16",
    "instagram_reel": "9:16",
    "facebook_post": "1.91:1",
    "facebook_story": "9:16",
    "linkedin_post": "1.91:1",
    "whatsapp": "1:1",
    "banner": "16:9",
}

# SED brand style modifiers for all image prompts
SED_STYLE_BASE = (
    "professional corporate photography, clean industrial aesthetic, "
    "South African solar industry, high-end B2B brand, "
    "sharp detail, studio lighting or golden hour natural light, "
    "no text unless specified"
)

SED_COLOR_DIRECTIVE = (
    "color palette: deep charcoal (#333333) backgrounds or clean white, "
    "orange accent elements (#E85A0C), minimal and modern"
)

NEGATIVE_PROMPT = (
    "cartoon, anime, illustration, clipart, amateur, blurry, "
    "residential consumer aesthetic, fake hardware, incorrect solar panels, "
    "watermark, logo overlay, text overlay, nsfw"
)

PLATFORM_VISUAL_STYLES = {
    "instagram": "cinematic, premium lifestyle, modern solar tech, aspirational",
    "facebook": "professional, approachable, informative, trust-building",
    "linkedin": "corporate, executive, industrial, authoritative",
    "whatsapp": "clean, simple, product-focused, clear",
}

CONTENT_TYPE_VISUAL_DIRECTION = {
    "stock_arrival": "warehouse setting with solar panels/inverters neatly stacked, "
                     "Johannesburg industrial warehouse aesthetic, orange brand elements",
    "educational": "clean infographic-style background, solar equipment detail shot, "
                   "professional diagram aesthetic",
    "product_showcase": "product hero shot, white or dark background, "
                        "studio lighting, brand panel/inverter/battery in focus",
    "c_and_i": "large commercial rooftop solar array, South African commercial building, "
               "aerial or eye-level perspective, impressive scale",
    "thought_leadership": "executive professional setting, clean modern office, "
                          "abstract solar/energy background, confident and authoritative",
    "installer_tip": "solar installer on rooftop or warehouse, PPE, professional setting, "
                     "South African context",
}


class DesignAgent:
    """
    Generates optimised image prompts for AI image generation tools.
    Ensures brand consistency and technical accuracy.
    """

    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    def _get_aspect_ratio(self, platform: str, content_type: str) -> str:
        if "story" in content_type or "reel" in content_type:
            return "9:16"
        return ASPECT_RATIOS.get(f"{platform}_post", "1:1")

    async def run(self, state: dict) -> dict:
        generated_content = state.get("generated_content", {})
        platform = state.get("platform", "instagram")
        content_type = state.get("content_type", "product_showcase")
        topic = state.get("topic", "")

        image_description = generated_content.get("image_description", "")
        aspect_ratio = self._get_aspect_ratio(platform, content_type)
        platform_style = PLATFORM_VISUAL_STYLES.get(platform, SED_STYLE_BASE)
        content_visual_dir = CONTENT_TYPE_VISUAL_DIRECTION.get(
            content_type, "professional solar equipment, clean industrial setting"
        )

        system_prompt = f"""{SED_MASTER_SYSTEM_PROMPT}

You are the Design Direction Agent. Generate a detailed, production-ready image generation prompt
for a Flux/SDXL/DALL-E model.

## SED Visual Identity
{SED_COLOR_DIRECTIVE}

## Rules
1. Be highly specific — describe composition, lighting, depth of field, perspective
2. Include "South African" setting modifiers where contextually appropriate
3. Never describe text/logo overlays — those are added in post-production
4. Always include the SED brand aesthetic: clean, premium, industrial-tech
5. Include negative prompts to avoid common AI image failures

## Output Format (JSON only)
{{
  "positive_prompt": "detailed image generation prompt",
  "negative_prompt": "things to avoid",
  "aspect_ratio": "{aspect_ratio}",
  "style": "photorealistic|cinematic|corporate",
  "guidance_scale": 7.5,
  "platform": "{platform}",
  "content_type": "{content_type}",
  "text_overlay_suggestion": "suggested text to overlay in post-production"
}}
"""

        user_prompt = f"""Create an image generation prompt for:
- Platform: {platform}
- Content type: {content_type}
- Topic: {topic}
- Content brief: {image_description}
- Platform visual style: {platform_style}
- Content visual direction: {content_visual_dir}
- Aspect ratio needed: {aspect_ratio}

Ensure the output is brand-accurate for SED Energy (Tier 1 solar distributor, Johannesburg).
"""

        try:
            response = await self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=800,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            raw = response.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1].lstrip("json").strip()

            prompt_data = json.loads(raw)
            return {
                "design_prompt": prompt_data.get("positive_prompt", ""),
                "design_data": prompt_data,
            }

        except Exception as e:
            logger.error(f"Design agent error: {e}", exc_info=True)
            # Fallback prompt
            fallback = (
                f"Professional solar equipment in a clean South African industrial warehouse, "
                f"{SED_COLOR_DIRECTIVE}, {SED_STYLE_BASE}, aspect ratio {aspect_ratio}"
            )
            return {
                "design_prompt": fallback,
                "design_data": {
                    "positive_prompt": fallback,
                    "negative_prompt": NEGATIVE_PROMPT,
                    "aspect_ratio": aspect_ratio,
                },
            }
