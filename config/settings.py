# config/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # GCP Project Configuration
    PROJECT_ID: str
    REGION: str = "us-central1"

    # GCS Bucket URIs
    INTAKE_RAW_BUCKET: str = "intake-ideas-bucket/raw"
    SKILL_DRAFTS_BUCKET: str = "enterprise-skillbank/drafts"
    SKILL_PROD_BUCKET: str = "enterprise-skillbank/production"

    # Database & Cache URIs
    REDIS_CACHE_URL: str = "redis://redis-master.default.svc.cluster.local:6379"
    FIRESTORE_REGISTRY_COLLECTION: str = "skill_registry"
    FIRESTORE_SESSION_STORE: str = "live_chat_sessions"
    FIRESTORE_INTAKE_SESSION_STORE: str = "intake_chat_sessions"
    FIRESTORE_GEM_CREATOR_SESSION_STORE: str = "gem_creator_sessions"

    # BigQuery Audit Database
    BQ_DATASET_ID: str = "agentic_workflow_metrics"
    BQ_AUDIT_TABLE: str = "worker_execution_logs"

    # Cloud Tasks Configuration
    TASK_QUEUE_NAME: str = "worker-dispatch-queue"
    WORKER_SERVICE_URL: str  # Base URL of internal Worker Cloud Run/GKE service

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


# Instantiate global settings object to be imported across agents and services
settings = Settings()