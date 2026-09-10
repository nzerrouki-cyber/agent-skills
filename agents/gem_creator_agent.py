# agents/gem_creator_agent.py
import re
from google.genai import types

from agents.base_agent import BaseAgent
from config.settings import settings
from services.session_store import SessionStoreService
from services.discovery_engine import DiscoveryEngineService
from models.schemas import IntakeSessionState, AisleSkill


class GemCreatorAgent(BaseAgent):
    """Interactive Gem Authoring Agent using Vertex AI Data Store RAG for skill baselines."""

    def __init__(self):
        super().__init__()
        self.session_store = SessionStoreService(
            collection_name=settings.FIRESTORE_GEM_CREATOR_SESSION_STORE
        )
        self.discovery_engine = DiscoveryEngineService()

    async def _get_gem_creator_system_instruction(self) -> str:
        """Retrieves promoted Gem Creator Meta-Skill directly from Production GCS / Redis."""
        prompt_content, _, _ = await self.get_promoted_skill_prompt("SKILL_GEM_CREATOR")
        return prompt_content

    def _generate_fallback_skill_id(self, session_id: str) -> str:
        clean_session = re.sub(r'[^a-zA-Z0-9]', '_', session_id).upper()
        return f"SKILL_GEM_{clean_session[:12]}"

    async def process_intake_pathway(self, session_id: str, user_payload: str) -> str:
        session: IntakeSessionState = await self.session_store.get_session(session_id)
        system_instruction = await self._get_gem_creator_system_instruction()

        # 1. Dynamic RAG query against Vertex AI Search Data Store for reference skill baselines
        reference_skill_context = await self.discovery_engine.search_datastore(
            datastore_id="system-core-ds",
            query_text=user_payload,
            top_k=3
        )

        history_context = "\n".join([
            f"{msg.sender.upper()}: {msg.content}" for msg in session.conversation_history
        ])

        # 2. Inject retrieved skill context into model prompt
        user_prompt = f"""CONVERSATION HISTORY:
{history_context}

RETRIEVED REFERENCE SKILL BASELINES (FROM VERTEX AI DATASTORE):
{reference_skill_context}

CURRENT ACTIVE USER PAYLOAD:
{user_payload}"""

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

        # Extract routing/schema metadata using BaseAgent metadata extractor
        extracted_meta = self.extract_header_metadata(f"{user_payload}\n{agent_reply}")
        updated_collected_fields = {**session.collected_fields, **extracted_meta}

        await self.session_store.update_turn(
            session_id=session_id,
            user_message=user_payload,
            agent_response=agent_reply,
            next_turn=next_turn,
            updated_fields=updated_collected_fields
        )

        # Extract generated markdown block using BaseAgent utility
        raw_skill_md = self.extract_markdown_block(agent_reply)
        if raw_skill_md:
            skill_id = extracted_meta.get("skill_id") or self._generate_fallback_skill_id(session_id)
            
            target_ds = extracted_meta.get("target_datastore_id") or updated_collected_fields.get("target_datastore_id")
            category = extracted_meta.get("category") or updated_collected_fields.get("category")
            schema_name = extracted_meta.get("output_schema") or updated_collected_fields.get("output_schema", "InnovationIntakeResult")
            
            agent_name = extracted_meta.get("agent_name") or updated_collected_fields.get("agent_name", f"{skill_id.lower()}_specialist")
            title = extracted_meta.get("title") or updated_collected_fields.get("title", skill_id.replace("_", " ").title())
            description = extracted_meta.get("description") or updated_collected_fields.get("description", "")

            # Write draft to GCS if target_datastore_id and category have been gathered
            if target_ds and category:
                skill_contract = AisleSkill(
                    skill_id=skill_id,
                    agent_name=agent_name,
                    title=title,
                    description=description,
                    category=category,
                    target_datastore_id=target_ds,
                    output_schema=schema_name,
                    routing_signals=updated_collected_fields.get("routing_signals", []),
                    tool_names=updated_collected_fields.get("tool_names", []),
                    instructions_markdown=raw_skill_md
                )

                formatted_skill = skill_contract.to_yaml_markdown()

                bucket_parts = settings.SKILL_DRAFTS_BUCKET.strip("/").split("/", 1)
                bucket_name = bucket_parts[0]
                prefix = bucket_parts[1] if len(bucket_parts) > 1 else ""
                blob_path = f"{prefix}/{skill_id}.md" if prefix else f"{skill_id}.md"

                await self.gcs_service.upload_string(
                    bucket_name=bucket_name,
                    blob_name=blob_path,
                    content=formatted_skill,
                    content_type="text/markdown"
                )

        return agent_reply