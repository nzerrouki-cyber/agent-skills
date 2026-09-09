# agents/intake_agent.py
from google.genai import types
from agents.base_agent import BaseAgent
from config.settings import settings
from services.session_store import SessionStoreService
from services.intake_webhook import IntakeWebhookService
from models.schemas import IntakeSessionState, SessionStatus

class IntakeAgent(BaseAgent):
    """Stateful WebSocket Intake Agent guiding users through innovation intake questions."""

    def __init__(self):
        super().__init__()
        self.session_store = SessionStoreService(
            collection_name=settings.FIRESTORE_INTAKE_SESSION_STORE
        )
        self.webhook_service = IntakeWebhookService()

    async def _get_intake_system_instruction(self) -> str:
        """Retrieves promoted Intake System Skill directly from Production GCS / Redis."""
        prompt_content, _, _ = await self.get_promoted_skill_prompt("SKILL_INTAKE")
        return prompt_content

    async def handle_user_message(self, session_id: str, user_message: str) -> dict:
        """Processes a chat turn over WebSockets, persisting session state and executing completion handoffs."""
        session: IntakeSessionState = await self.session_store.get_session(session_id)
        system_instruction = await self._get_intake_system_instruction()

        history_context = "\n".join([
            f"{msg.sender.upper()}: {msg.content}" for msg in session.conversation_history
        ])
        user_prompt = f"CONVERSATION HISTORY:\n{history_context}\n\nUSER INPUT:\n{user_message}"

        response = await self.genai_client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2
            )
        )

        agent_reply = response.text or ""
        next_turn = session.current_turn + 1

        # Extract any metadata provided by user or agent turn.
        extracted_meta = self.extract_header_metadata(f"{user_message}\n{agent_reply}")
        updated_collected_fields = {**session.collected_fields, **extracted_meta}
        
        # Updates session, conversation history and active chat turn session.
        await self.session_store.update_turn(
            session_id=session_id,
            user_message=user_message,
            agent_response=agent_reply,
            next_turn=next_turn,
            updated_fields=updated_collected_fields
        )

        # Enforce exact status sentinel matching to prevent premature handoff.
        is_completed = "[STATUS: COMPLETED]" in agent_reply
        # Once session is complete, the intake and category is stored and pushed to intake GCS via webhook function.
        if is_completed:
            target_ds = updated_collected_fields.get("target_datastore_id", "default-ds")
            category = updated_collected_fields.get("category", "Architecture Review")

            await self.session_store.mark_completed(
                session_id=session_id,
                category=category,
                target_datastore_id=target_ds
            )

            await self.webhook_service.convert_and_upload(
                session_id=session_id,
                fields=updated_collected_fields,
                target_datastore_id=target_ds,
                category=category
            )

        return {
            "reply": agent_reply,
            "session_id": session_id,
            "turn": next_turn,
            "status": SessionStatus.COMPLETED.value if is_completed else SessionStatus.IN_PROGRESS.value
        }