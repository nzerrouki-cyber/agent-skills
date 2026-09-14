# config/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # GCP Project Configuration
    PROJECT_ID: str
    REGION: str = "us-central1"

    # Apigee Gateway for LLM Traffic
    APIGEE_GATEWAY_URL: str | None = None
    APIGEE_API_KEY: str | None = None

    # GCS Bucket URIs
    INTAKE_RAW_BUCKET: str = "intake-ideas-bucket/raw"
    SKILL_DRAFTS_BUCKET: str = "enterprise-skillbank/drafts"
    SKILL_PROD_BUCKET: str = "enterprise-skillbank/production"

    # Database & Cache URIs
    REDIS_CACHE_URL: str = "redis://10.0.0.3:6379"
    FIRESTORE_REGISTRY_COLLECTION: str = "skill_registry"
    FIRESTORE_SESSION_STORE: str = "live_chat_sessions"
    FIRESTORE_INTAKE_SESSION_STORE: str = "intake_chat_sessions"
    FIRESTORE_GEM_CREATOR_SESSION_STORE: str = "gem_creator_sessions"

    # BigQuery Audit Database
    BQ_DATASET_ID: str = "agentic_workflow_metrics"
    BQ_AUDIT_TABLE: str = "worker_execution_logs"

    # Cloud Tasks & Cloud Run Job Configuration
    TASK_QUEUE_NAME: str = "worker-dispatch-queue"
    WORKER_SERVICE_URL: str = "https://router-service-url.run.app"
    WORKER_JOB_NAME: str = "projects/your-project/locations/us-central1/jobs/worker-agent-job"
    WORKER_SERVICE_ACCOUNT_EMAIL: str = "worker-invoker@your-project.iam.gserviceaccount.com"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


# Instantiate global settings object
settings = Settings()