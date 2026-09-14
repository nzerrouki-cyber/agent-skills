# services/cloud_run_jobs.py
import json
import logging
from google.cloud import run_v2
from config.settings import settings
from services.base_service import BaseService

logger = logging.getLogger(__name__)


class CloudRunJobsClient(BaseService):
    """Triggers ephemeral Cloud Run Job executions for worker agent tasks."""

    def __init__(self):
        super().__init__()
        self.client = run_v2.JobsAsyncClient()
        self.job_name = getattr(
            settings,
            "WORKER_JOB_NAME",
            f"projects/{self.project_id}/locations/{self.region}/jobs/worker-agent-job"
        )

    async def trigger_worker_job(self, payload: dict) -> str:
        """Launches a Cloud Run Job execution, passing the task payload via environment overrides."""
        payload_json = json.dumps(payload)

        request = run_v2.RunJobRequest(
            name=self.job_name,
            overrides=run_v2.RunJobRequest.Overrides(
                container_overrides=[
                    run_v2.RunJobRequest.Overrides.ContainerOverride(
                        env=[
                            run_v2.EnvVar(name="TASK_PAYLOAD", value=payload_json)
                        ]
                    )
                ]
            )
        )

        try:
            operation = await self.client.run_job(request=request)
            logger.info(f"Triggered Cloud Run Job '{self.job_name}' for skill '{payload.get('skill_id')}'")
            return operation.operation.name
        except Exception as e:
            logger.error(f"Failed to trigger Cloud Run Job '{self.job_name}': {str(e)}")
            raise e