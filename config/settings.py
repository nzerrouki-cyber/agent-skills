from pydantic_settings import BaseSettings

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
    
    # BigQuery Audit Database
    BQ_DATASET_ID: str = "agentic_workflow_metrics"
    BQ_AUDIT_TABLE: str = "worker_execution_logs"
    
    # Cloud Tasks Configuration
    TASK_QUEUE_NAME: str = "worker-dispatch-queue"
    WORKER_SERVICE_URL: str  # The base URL of the internal Worker Cloud Run/GKE service

    class Config:
        env_file = ".env"
        case_sensitive = True

# Instantiate a global settings object to be imported by agents/services
settings = Settings()