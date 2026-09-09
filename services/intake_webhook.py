# services/intake_webhook.py
from config.settings import settings
from services.base_service import BaseService
from services.gcs_service import GCSService


class IntakeWebhookService(BaseService):
    """Converts completed session fields into sanitized Markdown documents and uploads them to GCS."""

    def __init__(self):
        super().__init__()
        self.gcs_service = GCSService()
        self.bucket_name, self.prefix = self.clean_gcs_bucket_and_prefix(settings.INTAKE_RAW_BUCKET)

    async def convert_and_upload(
        self, 
        session_id: str, 
        fields: dict, 
        target_datastore_id: str, 
        category: str = "Architecture Review"
    ):
        """Converts completed intake session state into clean Markdown and persists to raw GCS bucket."""
        markdown_content = f"""# Innovation Intake Submission
**Submission ID:** {session_id}  
**Target Datastore ID:** {target_datastore_id}  
**Category:** {category}  

## Intake Details
"""

        for key, value in fields.items():
            if key in ["target_datastore_id", "category", "session_id"]:
                continue

            section_title = key.replace("_", " ").title()
            markdown_content += f"### {section_title}\n"

            if isinstance(value, list):
                for item in value:
                    markdown_content += f"- {item}\n"
                markdown_content += "\n"
            else:
                markdown_content += f"{value}\n\n"

        blob_path = (
            f"{self.prefix}/{session_id}_intake.md"
            if self.prefix
            else f"{session_id}_intake.md"
        )

        await self.gcs_service.upload_string(
            bucket_name=self.bucket_name,
            blob_name=blob_path,
            content=markdown_content.strip(),
            content_type="text/markdown",
        )