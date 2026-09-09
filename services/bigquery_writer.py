# services/bigquery_writer.py
import asyncio
from datetime import datetime, timezone
from typing import Any
from google.cloud import bigquery
from config.settings import settings
from services.base_service import BaseService

class BigQueryWriterService(BaseService):
    def __init__(self):
        super().__init__()
        self.client = bigquery.Client(project=self.project_id)
        self.table_id = f"{self.project_id}.{settings.BQ_DATASET_ID}.{settings.BQ_AUDIT_TABLE}"

    # Writes final results payload to the BigQuery DB
    async def write_audit_log(
        self,
        payload: dict[str, Any],
        skill_id: str | None = None,
        generation_id: str | None = None,
    ) -> None:
        """Persists Pydantic audit results to BigQuery."""
        row_to_insert = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "skill_id": skill_id,
            "generation_id": generation_id,
            "summary": payload.get("summary"),
            "markdown_report": payload.get("markdown_report"),
            "idea_score": payload.get("idea_score", payload.get("risk_score")),
            "score_classification": payload.get("score_classification", payload.get("risk_category")),
            "recommendation_details": payload.get("recommendation_details", []),
            "compliance_flags": payload.get("compliance_flags", payload.get("key_findings", [])),
        }

        errors = await asyncio.to_thread(
            self.client.insert_rows_json,
            table=self.table_id,
            json_rows=[row_to_insert],
        )

        if errors:
            raise RuntimeError(f"BigQuery insertion failed: {errors}")