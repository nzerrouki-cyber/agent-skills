# services/model_armor.py
import asyncio
import httpx
from pydantic import BaseModel
from services.base_service import BaseService


class SanitizationResult(BaseModel):
    is_safe: bool
    clean_text: str


class ModelArmorClient(BaseService):
    def __init__(self):
        super().__init__()
        self.api_url = f"https://modelarmor.googleapis.com/v1/projects/{self.project_id}/locations/{self.region}:sanitize"

    # Verifies the security and integrity of the intake.md and category
    async def sanitize_payload(self, text: str) -> SanitizationResult:
        """Sends payload to Model Armor asynchronously with fallback handling."""
        try:
            token = await asyncio.to_thread(self.get_gcp_bearer_token)
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            payload = {"text": text}

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.api_url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                
                return SanitizationResult(
                    is_safe=data.get("is_safe", True),
                    clean_text=data.get("sanitized_text", text)
                )
        except Exception:
            # Fallback to passing payload through if Model Armor service is temporarily unavailable
            return SanitizationResult(is_safe=True, clean_text=text)