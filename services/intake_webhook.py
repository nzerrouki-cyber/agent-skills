from google.cloud import storage
import httpx
from config.settings import settings

class IntakeWebhookService:
    def __init__(self):
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket("intake-ideas-bucket")

    async def convert_and_upload(self, session_id: str, fields: dict, category: str):
        """Converts completed session JSON into Markdown and writes to GCS."""
        
        # 1. Construct Markdown Document
        markdown_content = f"""# Innovation Intake Submission
**Submission ID:** {session_id}  
**Category:** {category}  

## Intake Details
"""
        for key, value in fields.items():
            markdown_content += f"### {key.replace('_', ' ').title()}\n{value}\n\n"

        # 2. Option A: After converted into markdown Direct Write to GCS (Fast Path)
        blob_path = f"raw/{session_id}_intake.md"
        blob = self.bucket.blob(blob_path)
        blob.upload_from_string(markdown_content, content_type="text/markdown")

        # 3. Option B: Call Cloud Function / AppsScript Webhook (if external processing needed)
        # async with httpx.AsyncClient() as client:
        #     await client.post(
        #         settings.CONVERSION_WEBHOOK_URL,
        #         json={"session_id": session_id, "markdown": markdown_content}
        #     )