# scripts/seed_skills.py
import os
import glob
import asyncio
from agents.base_agent import BaseAgent
from services.gcs_service import GCSService
from services.firestore_client import FirestoreClient
from config.settings import settings
from utils.logger import logger


async def bootstrap_pipeline():
    """Seeds foundational system and worker skills into GCS Production and Firestore."""
    base_agent = BaseAgent()
    gcs_service = GCSService()
    firestore_client = FirestoreClient()

    prod_bucket_parts = settings.SKILL_PROD_BUCKET.strip("/").split("/", 1)
    prod_bucket_name = prod_bucket_parts[0]
    prefix = prod_bucket_parts[1] if len(prod_bucket_parts) > 1 else ""

    seed_files = glob.glob("seeds/*.md")
    if not seed_files:
        logger.warning("No seed markdown files found in 'seeds/' directory.")
        return

    logger.info(f"Starting bootstrap seeding for {len(seed_files)} skill files...")

    for file_path in seed_files:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_content = f.read()

        try:
            frontmatter, _ = base_agent.parse_yaml_frontmatter(raw_content)
            skill_id = frontmatter["skill_id"]
            blob_name = f"{prefix}/{skill_id}.md" if prefix else f"{skill_id}.md"

            # 1. Upload to Production GCS Bucket
            await gcs_service.upload_string(
                bucket_setting=prod_bucket_name,
                blob_name=blob_name,
                content=raw_content,
                content_type="text/markdown"
            )

            prod_uri = f"gs://{prod_bucket_name}/{blob_name}"

            # 2. Index in Firestore Skill Registry
            registry_payload = {
                "skill_id": skill_id,
                "agent_name": frontmatter.get("agent_name", "generic_specialist"),
                "title": frontmatter.get("title", skill_id),
                "description": frontmatter.get("description", ""),
                "active_version": frontmatter.get("active_version", "1.0.0"),
                "category": frontmatter.get("category", "Architecture Review"),
                "target_datastore_id": frontmatter.get("target_datastore_id", "default-ds"),
                "output_schema": frontmatter.get("output_schema", "InnovationIntakeResult"),
                "routing_signals": frontmatter.get("routing_signals", []),
                "tool_names": frontmatter.get("tool_names", []),
                "gcs_uri": prod_uri,
                "generation_id": "1",
                "checksum": "seeded_initial_version",
                "status": "ACTIVE"
            }

            await firestore_client.upsert_skill_registry_index(registry_payload)
            logger.info(f"Successfully seeded and indexed: '{skill_id}'")

        except Exception as e:
            logger.error(f"Failed to seed skill file '{file_path}': {str(e)}")

    logger.info("Pipeline bootstrapping complete.")


if __name__ == "__main__":
    asyncio.run(bootstrap_pipeline())