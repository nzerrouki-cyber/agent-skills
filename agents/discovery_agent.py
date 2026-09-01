 # <skill_id, generation_id, target_datastore_id, skill_gcs_uri, intake_uri>
from services.firestore_client import FirestoreClient
from services.cloud_tasks import CloudTasksClient
from services.gcs_service import GCSService
from services.model_armor import ModelArmorClient
from models.schemas import TaskPayload 

class DiscoveryAgent:
    def __init__(self):
        self.firestore = FirestoreClient()
        self.task_queue = CloudTasksClient()
        # Instantiate GCS and Model Armor services
        self.gcs_service = GCSService()
        self.model_armor = ModelArmorClient()
        
    async def process_and_enqueue(self, event_payload: dict):
        """Processes GCS event, sanitizes input, categorizes, fetches skill, and queues task."""
        
        # 1. Parse Intake URI from the Eventarc payload
        bucket = event_payload.get("bucket")
        name = event_payload.get("name")
        intake_uri = f"gs://{bucket}/{name}"
        
        # 2. Download the raw Markdown text using GCSService
        raw_intake_text = await self.gcs_service.download_blob_as_text(bucket, name)
        
        # 3. Sanitize the text using Model Armor
        sanitization_result = await self.model_armor.sanitize_payload(raw_intake_text)
        if not sanitization_result.is_safe:
            raise ValueError(f"Malicious payload detected in {intake_uri}")

        # 4. Categorize the Intake using the sanitized text
        category = await self._categorize_submission(sanitization_result.clean_text)
        
        # 5. Retrieve Promoted Skill from the Skill Index Registry (Firestore)
        skill_record = await self.firestore.get_active_skill_by_category(category)
        
        if not skill_record:
            raise ValueError(f"No promoted skill found in registry for category: {category}")

        # 6. Construct the precise TaskPayload required by the Worker Pod
        payload = TaskPayload(
            skill_id=skill_record["skill_id"],
            generation_id=skill_record["generation_id"],
            target_datastore_id=skill_record["target_datastore_id"],
            skill_gcs_uri=skill_record["gcs_uri"],
            intake_uri=intake_uri
        )
        
        # 7. Enqueue to the Cloud Tasks throttled queue
        await self.task_queue.enqueue_worker_task(
            queue_name="worker-dispatch-queue",
            endpoint=f"/worker/{category}",
            payload=payload.model_dump()
        )