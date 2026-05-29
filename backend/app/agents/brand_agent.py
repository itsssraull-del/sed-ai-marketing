"""
SED Energy - Brand Compliance Agent
Validates all generated content against SED brand guidelines.
Catches hallucinations, incorrect product references, and off-brand messaging.
"""
import logging
import json
from anthropic import AsyncAnthropic
from app.config import settings
from app.core.prompts import SED_MASTER_SYSTEM_PROMPT
from app.core.brand import SED_BRANDS_DISTRIBUTED, SED_BRAND

logger = logging.getLogger("sed-ai.brand-agent")

APPROVED_BRANDS = list(SED_BRANDS_DISTRIBUTED.keys())

BRAND_RULES = [
    {"rule": "no_unapproved_brands", "description": "Only reference approved brands: " + ", ".join(APPROVED_BRANDS)},
    {"rule": "no_invented_specs", "description": "No specific wattage/capacity/warranty unless verified in context"},
    {"rule": "no_pricing", "description": "Never include specific pricing unless explicitly provided in context"},
    {"rule": "correct_company_name", "description": "Company is 'SED Energy' or 'Solar Energy Distributor', never just 'SED'"},
    {"rule": "b2b_tone", "description": "Content must target B2B audience (installers, EPCs, commercial buyers) not consumers"},
    {"rule": "sa_context", "description": "Content should reflect South African solar market context"},
    {"rule": "no_false_claims", "description": "No superlatives like 'lowest price', 'only supplier', 'guaranteed stock'"},
    {"rule": "contact_info_accurate", "description": "Contact info must match: 010 006 8246 | info@sed.energy | +27 79 748 6483"},
]

SEVERITY_MAP = {
    "no_unapproved_brands": "critical",
    "no_invented_specs": "critical",
    "no_pricing": "high",
    "correct_company_name": "high",
    "b2b_tone": "medium",
    "sa_context": "low",
    "no_false_claims": "high",
    "contact_info_accurate": "high",
}


class BrandComplianceAgent:
    """
    Validates content against SED brand guidelines.
    Provides confidence scoring and flagging for human review.
    """

    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def run(self, state: dict) -> dict:
        content = state.get("generated_content", {})
        if not content:
            return {"brand_check_passed": True, "brand_issues": []}

        content_text = content.get("body", "") + " " + content.get("caption", "")
        if content.get("whatsapp_message"):
            content_text += " " + content.get("whatsapp_message", "")

        system_prompt = f"""{SED_MASTER_SYSTEM_PROMPT}

You are the Brand Compliance Agent. Review content for brand accuracy and safety.

## Brand Rules to Check
{json.dumps(BRAND_RULES, indent=2)}

## Approved Brands (ONLY these may be referenced)
{', '.join(APPROVED_BRANDS)}

## Output Format (JSON)
{{
  "passed": true/false,
  "overall_risk": "low|medium|high|critical",
  "issues": [
    {{
      "rule": "rule_name",
      "severity": "low|medium|high|critical",
      "description": "what's wrong",
      "offending_text": "the problematic text",
      "suggested_fix": "how to fix it"
    }}
  ],
  "corrections": "Corrected version of the content (only if minor fixes needed)",
  "confidence_score": 0.0-1.0
}}
"""

        try:
            response = await self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1000,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"Review this content for brand compliance:\n\n{content_text}"
                }],
            )
            raw = response.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1].lstrip("json").strip()

            result = json.loads(raw)
            issues = result.get("issues", [])
            has_critical = any(i.get("severity") == "critical" for i in issues)
            passed = result.get("passed", True) and not has_critical

            # Apply auto-corrections for minor issues
            if not passed and result.get("corrections") and result.get("overall_risk") in ["low", "medium"]:
                content["body"] = result["corrections"]
                passed = True
                issues = [i for i in issues if i.get("severity") not in ["high", "critical"]]

            return {
                "brand_check_passed": passed,
                "brand_issues": issues,
                "generated_content": content,
                "confidence_score": float(result.get("confidence_score", 0.8)),
            }

        except Exception as e:
            logger.error(f"Brand compliance error: {e}", exc_info=True)
            # On error, flag for human review
            return {
                "brand_check_passed": False,
                "brand_issues": [{"rule": "check_failed", "severity": "high", "description": str(e)}],
                "confidence_score": 0.0,
            }

    def quick_check(self, text: str) -> dict:
        """Fast synchronous rule-based check (no LLM) for immediate validation"""
        issues = []

        # Check for unapproved brands
        known_solar_brands = [
            "JA Solar", "LONGi", "Canadian Solar", "Jinko", "Trina", "Huawei",
            "SMA", "Fronius", "ABB", "SolarEdge", "Enphase", "Growatt", "Deye",
        ]
        for brand in known_solar_brands:
            if brand.lower() in text.lower():
                issues.append({
                    "rule": "no_unapproved_brands",
                    "severity": "critical",
                    "description": f"Unapproved brand mentioned: {brand}",
                })

        # Check contact info
        if "010 006" in text and "8246" not in text:
            issues.append({"rule": "contact_info_accurate", "severity": "high", "description": "Incomplete phone number"})

        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "method": "quick_check",
        }
