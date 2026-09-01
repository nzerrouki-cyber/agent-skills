from services.session_store import SessionStoreService
from services.intake_webhook import IntakeWebhookService
from google import genai
from config.settings import settings

class IntakeAgent:
    # Question Sequence Definition
    # This is just a protype for the questions the IntakeAgent will ask the user.
    INTAKE_QUESTIONS = [
        {"turn": 0, "field": "core_idea", "prompt": "Welcome! Please describe your Core Purpose & Target Audience."},
        {"turn": 1, "field": "input_types", "prompt": "What types of input data, files, or user requests will this system process?"},
        {"turn": 2, "field": "category_domain", "prompt": "Which domain category does this belong to? (e.g., Security, Architecture, SCM SOP)"},
        {"turn": 3, "field": "output_requirements", "prompt": "What specific output formatting or callouts are required?"}
    ]

    # Categories that each intake idea will be mapped to.
    CATEGORY_DATASTORE_MAP = {
        "Security & Compliance": "ciso-policy-ds",
        "Architecture Review": "csa-template-ds",
        "Supply Chain SOP": "scm-sop-ds"
    }

    def __init__(self):
        self.session_store = SessionStoreService()
        self.webhook_service = IntakeWebhookService()
        self.ai_client = genai.Client()

    async def process_active_turn(self, session_id: str, user_input: str) -> str:
        """Processes one active turn in the intake loop."""
        session = await self.session_store.get_session(session_id)

        if session.status == "COMPLETED":
            return "This intake session is already completed and submitted."

        current_turn = session.current_turn
        question_config = self.INTAKE_QUESTIONS[current_turn]

        # 1. Update collected fields with current turn response
        session.collected_fields[question_config["field"]] = user_input

        # 2. Check if more questions remain
        next_turn = current_turn + 1
        if next_turn < len(self.INTAKE_QUESTIONS):
            next_prompt = self.INTAKE_QUESTIONS[next_turn]["prompt"]
            
            # Save progress to Live Chat Session Store
            await self.session_store.update_turn(
                session_id=session_id,
                user_message=user_input,
                agent_response=next_prompt,
                next_turn=next_turn,
                updated_fields=session.collected_fields
            )
            return next_prompt
        else:
            # 3. Finalize Intake Process
            return await self._finalize_intake(session)

    async def _finalize_intake(self, session: IntakeSessionState) -> str:
        """Categorizes submission, updates status to COMPLETED, and triggers handoff."""
        category = session.collected_fields.get("category_domain", "Architecture Review")
        target_datastore_id = self.CATEGORY_DATASTORE_MAP.get(category, "default-ds")

        # Mark completed in Session Store
        await self.session_store.mark_completed(
            session_id=session.session_id,
            category=category,
            target_datastore_id=target_datastore_id
        )

        # Trigger Webhook/Cloud Function to serialize to markdown and push to GCS
        await self.webhook_service.convert_and_upload(
            session_id=session.session_id,
            fields=session.collected_fields,
            category=category
        )

        return f"Thank you! Your intake submission is complete. Category assigned: '{category}'. Submission file generated and queued for processing."