# services/session_store.py
import time
from google.cloud import firestore
from config.settings import settings
from models.schemas import IntakeSessionState, ChatMessage, SessionStatus
from services.base_service import BaseService


class SessionStoreService(BaseService):
    def __init__(self, collection_name: str = settings.FIRESTORE_SESSION_STORE):
        super().__init__()
        self.db = self.get_firestore_client()
        self.collection = self.db.collection(collection_name)

    # Retrieve current session for the intake process
    async def get_session(self, session_id: str) -> IntakeSessionState:
        """Retrieves active turn state and conversation history."""
        doc_ref = self.collection.document(session_id)
        doc = await doc_ref.get()
        if not doc.exists:
            new_session = IntakeSessionState(session_id=session_id, user_id="anonymous")
            await doc_ref.set(new_session.model_dump())
            return new_session
        return IntakeSessionState(**doc.to_dict())

    # Update the active chat turn
    async def update_turn(
        self, 
        session_id: str, 
        user_message: str, 
        agent_response: str, 
        next_turn: int, 
        updated_fields: dict
    ):
        """Persists turn data, history, and extracted variables safely using merge semantics."""
        doc_ref = self.collection.document(session_id)
        now = time.time()
        
        history_updates = [
            ChatMessage(sender="user", content=user_message, timestamp=now).model_dump(),
            ChatMessage(sender="agent", content=agent_response, timestamp=now + 0.01).model_dump()
        ]

        await doc_ref.set({
            "current_turn": next_turn,
            "conversation_history": firestore.ArrayUnion(history_updates),
            "collected_fields": updated_fields,
            "updated_at": now
        }, merge=True)

    # Update session to the "COMPLETED" status to trigger webhook
    async def mark_completed(self, session_id: str, category: str, target_datastore_id: str):
        """Updates session state to COMPLETED."""
        doc_ref = self.collection.document(session_id)
        await doc_ref.set({
            "status": SessionStatus.COMPLETED.value,
            "category": category,
            "target_datastore_id": target_datastore_id,
            "completed_at": time.time()
        }, merge=True)