# services/gcs_service.py
import asyncio
from google.cloud import storage
from services.base_service import BaseService


class GCSService(BaseService):
    def __init__(self):
        super().__init__()
        self.storage_client = storage.Client(project=self.project_id)

    async def download_blob_as_text(self, bucket_setting: str, blob_name: str) -> str:
        """Downloads a blob from GCS asynchronously, handling gs:// prefixes in bucket settings."""
        bucket_name, _ = self.clean_gcs_bucket_and_prefix(bucket_setting)
        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        text_bytes = await asyncio.to_thread(blob.download_as_bytes)
        return text_bytes.decode("utf-8")

    async def download_from_uri(self, uri: str) -> str:
        """Parses a gs:// URI (stripping fragments if present) and downloads content."""
        bucket_name, blob_name = self.parse_gcs_uri(uri)
        return await self.download_blob_as_text(bucket_setting=bucket_name, blob_name=blob_name)

    async def upload_string(self, bucket_setting: str, blob_name: str, content: str, content_type: str = "text/plain"):
        """Uploads a string to GCS asynchronously, handling gs:// prefixes in bucket settings."""
        bucket_name, _ = self.clean_gcs_bucket_and_prefix(bucket_setting)
        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        await asyncio.to_thread(
            blob.upload_from_string,
            content,
            content_type=content_type
        )

    async def copy_and_promote_blob(
        self, 
        source_bucket_setting: str, 
        source_blob_name: str, 
        dest_bucket_setting: str, 
        dest_blob_name: str
    ) -> str:
        """Copies draft skill to production bucket and returns the unique destination Generation ID."""
        source_bucket_name, _ = self.clean_gcs_bucket_and_prefix(source_bucket_setting)
        dest_bucket_name, _ = self.clean_gcs_bucket_and_prefix(dest_bucket_setting)

        def _execute_copy():
            source_bucket = self.storage_client.bucket(source_bucket_name)
            source_blob = source_bucket.blob(source_blob_name)
            dest_bucket = self.storage_client.bucket(dest_bucket_name)
            
            dest_blob = source_bucket.copy_blob(source_blob, dest_bucket, dest_blob_name)
            dest_blob.reload()
            return str(dest_blob.generation)

        return await asyncio.to_thread(_execute_copy)