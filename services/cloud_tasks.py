from google.cloud import tasks_v2
import json
from config.settings import settings

class CloudTasksClient:
    def __init__(self):
        self.client = tasks_v2.CloudTasksClient()
        # Instantiate the exact GCP Queue Path using the config settings
        self.queue_path = self.client.queue_path(
            settings.PROJECT_ID, 
            settings.REGION, 
            settings.TASK_QUEUE_NAME
        )

    async def enqueue_worker_task(self, endpoint_route: str, payload: dict):
        """Builds the HTTP task and enqueues it to the throttled queue."""
        
        # Point the task to the internal Worker Service URL + the specific category route
        url = f"{settings.WORKER_SERVICE_URL}{endpoint_route}"
        
        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": url,
                "headers": {"Content-type": "application/json"},
                "body": json.dumps(payload).encode(),
                # Use OIDC tokens to authenticate via Workload Identity
                "oidc_token": {"service_account_email": f"worker-invoker@{settings.PROJECT_ID}.iam.gserviceaccount.com"}
            }
        }

        # Dispatch to the Queue
        response = self.client.create_task(parent=self.queue_path, task=task)
        return response.name