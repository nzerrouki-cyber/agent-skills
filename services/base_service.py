# services/base_service.py
import google.auth
import google.auth.transport.requests
from google.cloud import firestore
from config.settings import settings

# Parent class for shared methods across all services.
class BaseService:
    """Abstract Base Service providing shared GCP configuration, authentication, and URI parsing utilities."""

    _firestore_async_client: firestore.AsyncClient | None = None

    def __init__(self):
        self.project_id = settings.PROJECT_ID
        self.region = settings.REGION

    # Retrieve firestore instances used for storing session data and the skill index registry.
    @classmethod
    def get_firestore_client(cls) -> firestore.AsyncClient:
        """Returns a singleton firestore.AsyncClient instance shared across services."""
        if cls._firestore_async_client is None:
            cls._firestore_async_client = firestore.AsyncClient(project=settings.PROJECT_ID)
        return cls._firestore_async_client

    @staticmethod
    def clean_gcs_bucket_and_prefix(bucket_setting: str) -> tuple[str, str]:
        """Cleans bucket settings that might contain 'gs://' or trailing slashes and subpaths."""
        clean = bucket_setting.replace("gs://", "").strip("/")
        parts = clean.split("/", 1)
        bucket_name = parts[0]
        prefix = parts[1] if len(parts) > 1 else ""
        return bucket_name, prefix

    @staticmethod
    def parse_gcs_uri(uri: str) -> tuple[str, str]:
        """Parses 'gs://bucket_name/blob_name#generation' into bucket and blob components."""
        clean_uri = uri.split("#")[0]  # Strips generation fragment anchors if present
        if not clean_uri.startswith("gs://"):
            raise ValueError(f"Invalid GCS URI format (must start with 'gs://'): '{uri}'")

        path_parts = clean_uri[5:].split("/", 1)
        if len(path_parts) != 2 or not path_parts[0] or not path_parts[1]:
            raise ValueError(f"Invalid GCS URI path structure: '{uri}'")

        return path_parts[0], path_parts[1]

    # Generates Google OAuth2.0 token for Model Armor REST API Requests and Service Accounts used by agents.
    @staticmethod
    def get_gcp_bearer_token(scopes: list[str] | None = None) -> str:
        """Acquires a refreshed GCP OAuth2 bearer token for Workload Identity / REST calls."""
        if scopes is None:
            scopes = ["https://www.googleapis.com/auth/cloud-platform"]

        credentials, _ = google.auth.default(scopes=scopes)
        credentials.refresh(google.auth.transport.requests.Request())
        return credentials.token