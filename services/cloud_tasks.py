# services/cloud_tasks.py
import json
from urllib.parse import quote
from google.cloud import tasks_v2
from config.settings import settings
from services.base_service import BaseService


class CloudTasksClient(BaseService):
    def __init__(self):
        super().__init__()
        self.client = tasks_v2.CloudTasksAsyncClient()
        self.queue_path = self.client.queue_path(
            self.project_id, self.region, settings.TASK_QUEUE_NAME
        )

    async def enqueue_worker_task(self, endpoint_route: str, payload: dict) -> str:
        """Builds the HTTP task with URL-encoded route paths and enqueues it to Cloud Tasks."""
        clean_route = endpoint_route.lstrip("/")
        route_parts = clean_route.split("/")
        encoded_route_parts = [quote(part, safe="") for part in route_parts]
        encoded_route = "/".join(encoded_route_parts)

        base_url = settings.WORKER_SERVICE_URL.rstrip("/")
        url = f"{base_url}/{encoded_route}"

        # Binds service account email dynamically from settings for Cloud Run OIDC
        service_account_email = getattr(
            settings, 
            "WORKER_SERVICE_ACCOUNT_EMAIL", 
            f"worker-invoker@{self.project_id}.iam.gserviceaccount.com"
        )

        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": url,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(payload).encode("utf-8"),
                "oidc_token": {
                    "service_account_email": service_account_email
                },
            }
        }

        response = await self.client.create_task(parent=self.queue_path, task=task)
        return response.name