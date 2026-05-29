"""
SED Energy - WhatsApp Business API Service
Sends messages via WhatsApp Business Cloud API.
"""
import logging
import httpx
from typing import Optional
from app.config import settings

logger = logging.getLogger("sed-ai.whatsapp-service")

WA_BASE = "https://graph.facebook.com/v19.0"


class WhatsAppService:
    """
    Sends WhatsApp messages using the Meta WhatsApp Business Cloud API.
    Supports text, image, video, document, and template messages.
    """

    def __init__(self):
        self.base_url = f"{WA_BASE}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        self.headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_API_TOKEN}",
            "Content-Type": "application/json",
        }

    async def send_text(self, to: str, message: str, preview_url: bool = False) -> dict:
        """Send a plain text message"""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"body": message, "preview_url": preview_url},
        }
        return await self._send(payload)

    async def send_image(self, to: str, image_url: str, caption: str = "") -> dict:
        """Send an image with optional caption"""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "image",
            "image": {"link": image_url, "caption": caption},
        }
        return await self._send(payload)

    async def send_document(self, to: str, doc_url: str, filename: str, caption: str = "") -> dict:
        """Send a PDF or document"""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "document",
            "document": {"link": doc_url, "caption": caption, "filename": filename},
        }
        return await self._send(payload)

    async def send_template(self, to: str, template_name: str, language: str = "en", components: list = None) -> dict:
        """Send an approved WhatsApp Business template"""
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language},
                "components": components or [],
            },
        }
        return await self._send(payload)

    async def send_to_group_broadcast(self, phone_numbers: list, message: str) -> list:
        """
        Send a message to a list of phone numbers (broadcast).
        WhatsApp Cloud API doesn't directly post to groups — this sends individually.
        For true group posting, use a WhatsApp gateway like Ultramsg or WA Web API.
        """
        results = []
        async with httpx.AsyncClient() as client:
            for number in phone_numbers:
                result = await self.send_text(number, message)
                results.append({"to": number, **result})
        return results

    async def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """Verify Meta webhook subscription"""
        if mode == "subscribe" and token == settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN:
            return challenge
        return None

    async def process_webhook(self, data: dict) -> list:
        """Parse incoming WhatsApp webhook events"""
        events = []
        try:
            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    for msg in messages:
                        events.append({
                            "type": "incoming_message",
                            "from": msg.get("from"),
                            "message_id": msg.get("id"),
                            "timestamp": msg.get("timestamp"),
                            "text": msg.get("text", {}).get("body", ""),
                            "message_type": msg.get("type"),
                        })
        except Exception as e:
            logger.error(f"Webhook parse error: {e}")
        return events

    async def _send(self, payload: dict) -> dict:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                msg_id = data.get("messages", [{}])[0].get("id", "")
                logger.info(f"WhatsApp message sent: {msg_id} to {payload.get('to')}")
                return {"success": True, "message_id": msg_id}
            except httpx.HTTPStatusError as e:
                logger.error(f"WhatsApp send error: {e.response.text}")
                return {"success": False, "error": e.response.text}
            except Exception as e:
                logger.error(f"WhatsApp send error: {e}")
                return {"success": False, "error": str(e)}
