# services/core_service.py
import logging
from google.genai import types

from config.settings import settings
from models.schemas import TaskPayload, get_schema_by_name
from services.firestore_client import FirestoreClient
from services.gcs_service import GCSService
from services.redis_cache import WorkerRedisCache
from services.discovery_engine import DiscoveryEngineService
from services.bigquery_writer import BigQueryWriterService

logger = logging.getLogger(__name__)


class CoreWorkflowService:
    """Centralized core service managing skill lifecycles, prompt assembly,
    and execution across router and worker containers."""

    def __init__(self, genai_client=None):
        self.firestore = FirestoreClient()
        self.gcs_service = GCSService()
        self.redis_cache = WorkerRedisCache()
        self.discovery_engine = DiscoveryEngineService()
        self.bq_writer = BigQueryWriterService()
        self.genai_client = genai_client

    async def list_available_skills(self, category: str | None = None) -> list[dict]:
        """Specification 1: Fetches all available active skills from the registry."""
        return await self.firestore.list_active_skills(category=category)

    async def load_skill_prompt(self, skill_id: str, generation_id: str | None = None) -> tuple[str, str]:
        """Specification 2 & 3: Resolves active skill prompt via Redis Cache or Production GCS.
        Writes to Redis MemoryStore on cache misses."""
        if not generation_id:
            record = await self.firestore.get_active_skill_by_id(skill_id)
            if not record:
                raise ValueError(f"Skill '{skill_id}' not found in active registry.")
            generation_id = str(record["generation_id"])
            gcs_uri = record["gcs_uri"]
        else:
            gcs_uri = f"gs://{settings.SKILL_PROD_BUCKET.strip('/')}/{skill_id}.md"

        # Check Redis Cache
        cached_prompt = await self.redis_cache.get_skill(skill_id, generation_id)
        if cached_prompt:
            return cached_prompt, generation_id

        # Cache Miss: Download from GCS and write to Redis MemoryStore
        prompt_content = await self.gcs_service.download_from_uri(gcs_uri)
        await self.redis_cache.set_skill(skill_id, generation_id, prompt_content)
        return prompt_content, generation_id

    async def execute_skill_workflow(self, payload: TaskPayload, clean_system_prompt: str) -> dict:
        """Executes an agent task by combining user payload, dynamic RAG context,
        and system instructions via Gemini 2.5 Flash."""
        if not self.genai_client:
            raise ValueError("GenAI Client must be initialized on CoreWorkflowService before execution.")

        # 1. Fetch RAG Context from Target Datastore
        rag_context = await self.discovery_engine.search_datastore(
            datastore_id=payload.target_datastore_id,
            query_text=payload.intake_content,
            top_k=3
        )

        # 2. Resolve Pydantic Output Schema
        response_schema = get_schema_by_name(payload.output_schema)
        user_prompt = f"Intake Submission:\n{payload.intake_content}\n\nReference Material:\n{rag_context}"

        # 3. Call Gemini API (routed via Apigee Gateway if configured)
        response = await self.genai_client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=clean_system_prompt,
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=0.1
            )
        )

        # 4. Parse Structured Result
        try:
            if response.parsed is not None:
                audit_result = response.parsed.model_dump()
            else:
                audit_result = {
                    "summary": "Execution Completed with Unparsed Output",
                    "markdown_report": response.text or "No raw text generated."
                }
        except Exception as err:
            audit_result = {
                "summary": f"Execution Completed with Parsing Error: {str(err)}",
                "markdown_report": response.text or "No raw text generated."
            }

        # 5. Write to BigQuery Audit Log via Storage Write API
        await self.bq_writer.write_audit_log(
            payload=audit_result,
            skill_id=payload.skill_id,
            generation_id=payload.generation_id
        )

        return audit_result