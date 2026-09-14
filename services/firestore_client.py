# services/firestore_client.py
import time
import logging
from google.cloud import firestore
from config.settings import settings
from services.base_service import BaseService

logger = logging.getLogger(__name__)


class FirestoreClient(BaseService):
    def __init__(self):
        super().__init__()
        self.db = self.get_firestore_client()
        self.registry = self.db.collection(settings.FIRESTORE_REGISTRY_COLLECTION)

    async def list_active_skills(self, category: str | None = None) -> list[dict]:
        """Queries all active skills from the registry (Specification 1)."""
        try:
            if category:
                query = self.registry.where(
                    filter=firestore.FieldFilter("category", "==", category)
                ).where(
                    filter=firestore.FieldFilter("status", "==", "ACTIVE")
                )
            else:
                query = self.registry.where(
                    filter=firestore.FieldFilter("status", "==", "ACTIVE")
                )
            
            docs = query.stream()
            skills = []
            async for doc in docs:
                skills.append(doc.to_dict())
            return skills
        except Exception as e:
            logger.warning(f"Composite query failed, falling back to client-side filtering: {str(e)}")
            # Fallback for unbuilt composite indexes
            docs = self.registry.stream()
            skills = []
            async for doc in docs:
                data = doc.to_dict()
                if data.get("status") == "ACTIVE":
                    if not category or data.get("category") == category:
                        skills.append(data)
            return skills

    async def get_active_skill_by_id(self, skill_id: str) -> dict | None:
        """Queries the Skill Registry directly by skill_id."""
        doc_ref = self.registry.document(skill_id)
        doc = await doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            if data.get("status") == "ACTIVE":
                return data
        return None

    async def get_active_skill_by_datastore(self, datastore_id: str) -> dict | None:
        """Queries the Skill Registry for worker skills bound to target_datastore_id."""
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
            query = self.registry.where(
                filter=firestore.FieldFilter("target_datastore_id", "==", datastore_id)
            )
            docs = query.stream()
            async for doc in docs:
                data = doc.to_dict()
                if data.get("status") == "ACTIVE":
                    return data
        return None

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

    async def get_active_skill(self, identifier: str) -> dict | None:
        """Dual-lookup helper checking skill_id first, falling back to category."""
        record = await self.get_active_skill_by_id(identifier)
        if record:
            return record
        return await self.get_active_skill_by_category(identifier)

    async def upsert_skill_registry_index(self, skill_data: dict) -> None:
        """Inserts or updates a skill in the Skill Registry index."""
        skill_id = skill_data["skill_id"]
        doc_ref = self.registry.document(skill_id)
        payload = {
            **skill_data,
            "status": "ACTIVE",
            "updated_at": time.time()
        }
        await doc_ref.set(payload, merge=True)