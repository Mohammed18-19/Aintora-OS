"""
Meta WhatsApp Cloud API Client
Handles all outgoing messages to Meta's API.
"""
import httpx
import structlog
from typing import Optional, Any

logger = structlog.get_logger()

META_API_BASE = "https://graph.facebook.com/v19.0"


class WhatsAppClient:
    def __init__(self, phone_number_id: str, access_token: str):
        self.phone_number_id = phone_number_id
        self.access_token = access_token
        self.base_url = f"{META_API_BASE}/{phone_number_id}"
        self._headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    async def send_text(
        self, to: str, message: str, preview_url: bool = False
    ) -> dict:
        """Send a plain text message."""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self._normalize_number(to),
            "type": "text",
            "text": {"preview_url": preview_url, "body": message},
        }
        return await self._post("messages", payload)

    async def send_interactive_buttons(
        self, to: str, body: str, buttons: list[dict], header: Optional[str] = None
    ) -> dict:
        """Send an interactive message with up to 3 quick-reply buttons."""
        interactive = {
            "type": "button",
            "body": {"text": body},
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {"id": btn["id"], "title": btn["title"][:20]},
                    }
                    for btn in buttons[:3]
                ]
            },
        }
        if header:
            interactive["header"] = {"type": "text", "text": header}

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self._normalize_number(to),
            "type": "interactive",
            "interactive": interactive,
        }
        return await self._post("messages", payload)

    async def send_interactive_list(
        self, to: str, body: str, sections: list[dict], button_text: str = "Choose"
    ) -> dict:
        """Send a list message (for service selection)."""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self._normalize_number(to),
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {"text": body},
                "action": {
                    "button": button_text[:20],
                    "sections": sections,
                },
            },
        }
        return await self._post("messages", payload)

    async def mark_as_read(self, message_id: str) -> dict:
        """Mark a received message as read."""
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }
        return await self._post("messages", payload)

    async def _post(self, endpoint: str, payload: dict) -> dict:
        url = f"{self.base_url}/{endpoint}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.post(url, json=payload, headers=self._headers)
                data = resp.json()
                if resp.status_code not in (200, 201):
                    logger.error(
                        "whatsapp_api_error",
                        status=resp.status_code,
                        response=data,
                        endpoint=endpoint,
                    )
                return data
            except Exception as e:
                logger.error("whatsapp_client_exception", error=str(e))
                return {"error": str(e)}

    @staticmethod
    def _normalize_number(number: str) -> str:
        """Ensure number has country code, strip non-digits."""
        if not number:
            return ""

        normalized = "".join(c for c in number if c.isdigit() or c == "+")
        if normalized.startswith("00"):
            normalized = normalized[2:]
        if normalized.startswith("+"):
            return normalized[1:]

        digits = "".join(c for c in normalized if c.isdigit())
        if digits.startswith("212"):
            return digits
        if len(digits) <= 9:
            return "212" + digits.lstrip("0")
        return digits
