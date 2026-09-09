# agents/worker_agent.py
from google.genai import types

from agents.base_agent import BaseAgent
from models.schemas import TaskPayload, get_schema_by_name
from services.bigquery_writer import BigQueryWriterService
from services.discovery_engine import DiscoveryEngineService


class WorkerAgent(BaseAgent):
    """Stateless worker execution agent consuming tasks from Cloud Tasks."""

    def __init__(self, category: str = "default"):
        super().__init__()
        self.category = category
        self.bq_writer = BigQueryWriterService()
        self.discovery_engine = DiscoveryEngineService()

    async def execute_task(self, payload: TaskPayload) -> dict:
        """Executes worker task using inline sanitized content and dynamic output schema parsing."""

        # 1. Fetch skill prompt from Redis or GCS (if skill was not cached)
        skill_prompt = await self.redis_cache.get_skill(payload.skill_id, payload.generation_id)
        if not skill_prompt:
            skill_prompt = await self.gcs_service.download_from_uri(payload.skill_gcs_uri)
            await self.redis_cache.set_skill(payload.skill_id, payload.generation_id, skill_prompt)

        # Strip YAML frontmatter headers to avoid prompt context pollution
        clean_skill_prompt = self.strip_yaml_frontmatter(skill_prompt)

        # 2. Extract inline sanitized intake content from TaskPayload
        intake_content = payload.intake_content

        # 3. Dynamic RAG lookup against domain target_datastore_id to retrieve proper knowledge base files
        rag_context = await self.discovery_engine.search_datastore(
            datastore_id=payload.target_datastore_id,
            query_text=intake_content,
            top_k=3
        )

        # 4. Resolve output schema dynamically
        response_schema = get_schema_by_name(payload.output_schema)
        user_prompt = f"Intake Submission:\n{intake_content}\n\nReference Material:\n{rag_context}"

        # 5. Call Gemini 2.5 Flash with token-level constrained decoding
        response = await self.genai_client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=clean_skill_prompt,
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=0.1
            )
        )

        # Defensive handling for constrained JSON response deserialization
        try:
            if response.parsed is not None:
                audit_result = response.parsed.model_dump()
            else:
                audit_result = {
                    "summary": "Execution Completed with Unparsed Output",
                    "markdown_report": response.text or "No raw text generated."
                }
        except Exception as parsing_err:
            audit_result = {
                "summary": f"Execution Completed with Parsing Error: {str(parsing_err)}",
                "markdown_report": response.text or "No raw text generated."
            }

        # 6. Stream the final payload to the BigQuery DB via BigQuery Storage Write API
        await self.bq_writer.write_audit_log(
            payload=audit_result,
            skill_id=payload.skill_id,
            generation_id=payload.generation_id
        )

        return audit_result