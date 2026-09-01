from google.cloud import firestore
from models.schemas import IntakeSessionState, ChatMessage, SessionStatus
from config.settings import settings
import time

# Instantiate Live Session Chat Store, which stores the entire conversation payload within a GCP Firestore.
class SessionStoreService:
    def __init__(self):
        self.db = firestore.AsyncClient(project=settings.PROJECT_ID)
        self.collection = self.db.collection(settings.FIRESTORE_SESSION_STORE)

    async def get_session(self, session_id: str) -> IntakeSessionState:
        """Retrieves active turn state and conversation history."""
        doc_ref = self.collection.document(session_id)
        doc = await doc_ref.get()
        if not doc.exists:
            # Initialize new session state
            new_session = IntakeSessionState(session_id=session_id, user_id="anonymous")
            await doc_ref.set(new_session.model_dump())
            return new_session
        return IntakeSessionState(**doc.to_dict())

    async def update_turn(
        self, 
        session_id: str, 
        user_message: str, 
        agent_response: str, 
        next_turn: int, 
        updated_fields: dict
    ):
        """Persists turn data, history, and extracted intake variables."""
        doc_ref = self.collection.document(session_id)
        now = time.time()
        
        history_updates = [
            ChatMessage(sender="user", content=user_message, timestamp=now).model_dump(),
            ChatMessage(sender="agent", content=agent_response, timestamp=now + 0.01).model_dump()
        ]

        await doc_ref.update({
            "current_turn": next_turn,
            "conversation_history": firestore.ArrayUnion(history_updates),
            "collected_fields": updated_fields
        })

    async def mark_completed(self, session_id: str, category: str, target_datastore_id: str):
        """Updates session state to COMPLETED and sets the category mapping."""
        doc_ref = self.collection.document(session_id)
        await doc_ref.update({
            "status": SessionStatus.COMPLETED.value,
            "category": category,
            "target_datastore_id": target_datastore_id
        })