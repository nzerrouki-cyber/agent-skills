# agents/discovery_agent.py
# <skill_id, generation_id, target_datastore_id, skill_gcs_uri, intake_uri>
from agents.base_agent import BaseAgent
from models.schemas import TaskPayload
from services.cloud_tasks import CloudTasksClient
from services.model_armor import ModelArmorClient

class DiscoveryAgent(BaseAgent):
    """Event-driven routing agent using AisleSkill metadata for registry lookups."""

    def __init__(self):
        super().__init__()
        self.task_queue = CloudTasksClient()
        self.model_armor = ModelArmorClient()

    # Emits an eventarc trigger after an intake is added, discoveyr agent retrieves skil and enqueues task for the worker agent.
    async def process_and_enqueue(self, event_payload: dict):
        """Processes Eventarc GCS events, runs security checks, resolves active skills, and enqueues tasks."""
        bucket, name = self.extract_gcs_event_data(event_payload)
        raw_text = await self.gcs_service.download_blob_as_text(bucket, name)

        # 1. Extract metadata (skill_id or target_datastore_id) from intake header
        metadata = self.extract_header_metadata(raw_text)
        explicit_skill_id = metadata.get("skill_id")
        datastore_id = metadata.get("target_datastore_id", "default-ds")

        # 2. Sanitize payload via Model Armor
        sanitized = await self.model_armor.sanitize_payload(raw_text)
        if not sanitized.is_safe:
            raise ValueError(f"Malicious payload detected in gs://{bucket}/{name}")

        # 3. Registry Lookup: Check explicit skill_id first, fallback to target_datastore_id
        skill_record = None
        if explicit_skill_id:
            skill_record = await self.firestore.get_active_skill_by_id(explicit_skill_id)

        if not skill_record:
            skill_record = await self.firestore.get_active_skill_by_datastore(datastore_id)

        if not skill_record:
            raise ValueError(
                f"No active skill registered in Firestore for skill_id: '{explicit_skill_id}' "
                f"or target_datastore_id: '{datastore_id}'"
            )

        # 4. Build TaskPayload with immutable skill pointers and metadata
        payload = TaskPayload(
            skill_id=skill_record["skill_id"],
            generation_id=str(skill_record["generation_id"]),
            target_datastore_id=skill_record.get("target_datastore_id", datastore_id),
            output_schema=skill_record.get("output_schema", "InnovationIntakeResult"),
            skill_gcs_uri=skill_record["gcs_uri"],
            intake_content=sanitized.clean_text
        )

        # 5. Dispatch to Cloud Tasks worker queue
        await self.task_queue.enqueue_worker_task(
            endpoint_route=f"/worker/{payload.target_datastore_id}",
            payload=payload.model_dump()
        )