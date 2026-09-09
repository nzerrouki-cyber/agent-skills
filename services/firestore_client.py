# services/firestore_client.py
import time
from google.cloud import firestore
from config.settings import settings
from services.base_service import BaseService


class FirestoreClient(BaseService):
    def __init__(self):
        super().__init__()
        self.db = self.get_firestore_client()
        self.registry = self.db.collection(settings.FIRESTORE_REGISTRY_COLLECTION)

    # Retrieve skill from Skill Index Registry by skill id
    async def get_active_skill_by_id(self, skill_id: str) -> dict | None:
        """Queries the Skill Registry directly by skill_id."""
        doc_ref = self.registry.document(skill_id)
        doc = await doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            if data.get("status") == "ACTIVE":
                return data
        return None

    # Queries the skill by the target_datastore_id as a fallback
    async def get_active_skill_by_datastore(self, datastore_id: str) -> dict | None:
        """Queries the Skill Registry for worker skills bound to target_datastore_id with fallback handling."""
        try:
            query = self.registry.where(
                filter=firestore.FieldFilter("target_datastore_id", "==", datastore_id)
            ).where(
                filter=firestore.FieldFilter("status", "==", "ACTIVE")
            )
            docs = query.stream()
            async for doc in docs:
                return doc.to_dict()
        except Exception:
            # Single-field query fallback if composite index is not yet built
            query = self.registry.where(
                filter=firestore.FieldFilter("target_datastore_id", "==", datastore_id)
            )
            docs = query.stream()
            async for doc in docs:
                data = doc.to_dict()
                if data.get("status") == "ACTIVE":
                    return data
        return None

    # Queries for the skill based on category
    async def get_active_skill_by_category(self, category: str) -> dict | None:
        """Queries the Skill Registry by category."""
        query = self.registry.where(
            filter=firestore.FieldFilter("category", "==", category)
        ).where(
            filter=firestore.FieldFilter("status", "==", "ACTIVE")
        )
        docs = query.stream()
        async for doc in docs:
            return doc.to_dict()
        return None

    # Default method to retrieve skill by skill_id
    async def get_active_skill(self, identifier: str) -> dict | None:
        """Dual-lookup helper checking skill_id first, falling back to category."""
        record = await self.get_active_skill_by_id(identifier)
        if record:
            return record
        return await self.get_active_skill_by_category(identifier)

    # Inserts a new skill_id i.e index within the Skill Index Registry
    async def upsert_skill_registry_index(self, skill_data: dict) -> None:
        skill_id = skill_data["skill_id"]
        doc_ref = self.registry.document(skill_id)
        payload = {
            **skill_data,
            "status": "ACTIVE",
            "updated_at": time.time()
        }
        await doc_ref.set(payload, merge=True)