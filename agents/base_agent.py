# agents/base_agent.py
import re
import yaml
from google import genai
from google.genai import types

from config.settings import settings
from services.gcs_service import GCSService
from services.firestore_client import FirestoreClient
from services.redis_cache import WorkerRedisCache

class BaseAgent:
    """Abstract Base Agent providing shared GCP clients, YAML frontmatter manipulation, 
    metadata parsing, and prompt loading utilities across all workflow agents."""

    def __init__(self):
        self.gcs_service = GCSService()
        self.firestore = FirestoreClient()
        self.redis_cache = WorkerRedisCache()

        # Centralized Vertex AI Gemini Client instantiation
        self.genai_client = genai.Client(
            vertexai=True,
            project=settings.PROJECT_ID,
            location=settings.REGION,
        )

    # ---------------------------------------------------------
    # Shared GCS & Registry Helpers
    # ---------------------------------------------------------

    @staticmethod
    # Extracts the event payload and GCS bucket information when running eventarc triggers.
    def extract_gcs_event_data(event_payload: dict) -> tuple[str, str]:
        """Unwraps bucket name and object blob name from raw GCS notifications and Eventarc CloudEvents."""
        data = event_payload.get("data", event_payload)
        bucket = data.get("bucket")
        name = data.get("name")

        if not bucket or not name:
            raise ValueError(f"Invalid Eventarc/GCS payload structure: {event_payload}")

        return bucket, name

    # Retrieve a validated skill from the Production GCS / Redis Cache (if cached)
    async def get_promoted_skill_prompt(self, identifier: str) -> tuple[str, str, str]:
        """Fetches active skill prompt from Redis cache or Production GCS using dual lookup."""
        skill_record = await self.firestore.get_active_skill(identifier)
        if not skill_record:
            raise ValueError(f"No active skill found in registry for: '{identifier}'")

        skill_id = skill_record["skill_id"]
        generation_id = skill_record["generation_id"]
        gcs_uri = skill_record["gcs_uri"]

        cached_prompt = await self.redis_cache.get_skill(skill_id, generation_id)
        if cached_prompt:
            return cached_prompt, skill_id, generation_id

        prompt_content = await self.gcs_service.download_from_uri(gcs_uri)
        await self.redis_cache.set_skill(skill_id, generation_id, prompt_content)
        return prompt_content, skill_id, generation_id

    async def get_system_instruction_with_fallback(self, identifier: str, default_instruction: str) -> str:
        """Helper to fetch promoted prompts with fallback defaults."""
        try:
            prompt_content, _, _ = await self.get_promoted_skill_prompt(identifier)
            return prompt_content
        except Exception:
            return default_instruction

    # ---------------------------------------------------------
    # Shared Frontmatter & YAML Manipulation Methods
    # ---------------------------------------------------------

    @staticmethod
    def parse_yaml_frontmatter(raw_content: str) -> tuple[dict, str]:
        """Parses YAML frontmatter headers (---...---) and splits metadata from markdown body."""
        clean_content = raw_content.strip()
        pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
        match = re.search(pattern, clean_content, re.DOTALL)
        if not match:
            raise ValueError("Invalid Format: Missing required YAML frontmatter headers (---...---).")

        frontmatter = yaml.safe_load(match.group(1))
        if not isinstance(frontmatter, dict):
            raise ValueError("Invalid Frontmatter: Content header did not parse into a valid dictionary.")

        return frontmatter, match.group(2).strip()

    @staticmethod
    def strip_yaml_frontmatter(raw_content: str) -> str:
        """Strips existing YAML frontmatter headers if present, returning clean markdown body."""
        clean = raw_content.strip()
        pattern = r"^---\s*\n.*?\n---\s*\n(.*)$"
        match = re.search(pattern, clean, re.DOTALL)
        if match:
            return match.group(1).strip()
        return clean

    # Inject YAML metadata within skills
    def inject_yaml_frontmatter(
        self,
        skill_id: str,
        markdown_content: str,
        target_datastore_id: str,
        category: str,
        agent_name: str = "generic_specialist",
        title: str = "",
        description: str = "",
        routing_signals: list[str] | None = None,
        tool_names: list[str] | None = None,
        output_schema: str = "InnovationIntakeResult",
        active_version: str = "1.0.0",
        status: str = "DRAFT"
    ) -> str:
        # Injects standardized YAML frontmatter adhering to the AisleSkill specification.
        if not target_datastore_id or target_datastore_id.strip() in ["", "default-ds"]:
            raise ValueError(
                f"Cannot inject YAML frontmatter for skill '{skill_id}': "
                "A valid, explicit 'target_datastore_id' must be provided."
            )

        if not category or category.strip() in ["", "Architecture Review"]:
            raise ValueError(
                f"Cannot inject YAML frontmatter for skill '{skill_id}': "
                "A valid, explicit 'category' must be provided."
            )

        clean_body = self.strip_yaml_frontmatter(markdown_content)
        raw_bucket = settings.SKILL_PROD_BUCKET.strip("/")

        signals = routing_signals or []
        tools = tool_names or []

        signals_formatted = "\n".join([f'  - "{s}"' for s in signals])
        tools_formatted = "\n".join([f'  - "{t}"' for t in tools])

        yaml_header = f"""---
skill_id: "{skill_id}"
agent_name: "{agent_name}"
title: "{title if title else skill_id.replace('_', ' ').title()}"
description: "{description}"
active_version: "{active_version}"
category: "{category.strip()}"
target_datastore_id: "{target_datastore_id.strip()}"
output_schema: "{output_schema.strip()}"
routing_signals:
{signals_formatted if signals_formatted else "  []"}
tool_names:
{tools_formatted if tools_formatted else "  []"}
gcs_uri: "gs://{raw_bucket}/{skill_id}.md"
generation_id: "0"
status: "{status}"
---

"""
        return yaml_header + clean_body.lstrip()

    # ---------------------------------------------------------
    # Shared Text Processing & Parsing Utilities
    # ---------------------------------------------------------

    @staticmethod
    def extract_markdown_block(text: str) -> str | None:
        """Extracts text within markdown code fences (```markdown ... ``` or ``` ... ```)."""
        if not text:
            return None
        match = re.search(r"```(?:markdown)?\n(.*?)```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    @staticmethod
    def extract_header_metadata(text: str) -> dict[str, str]:
        """Extracts standard key-value routing fields from markdown headers or plain text."""
        metadata = {}

        patterns = {
            "target_datastore_id": [
                r"\*\*Target Datastore ID:\*\*\s*(.+)",
                r"Target Datastore ID:\s*(.+)",
                r'target_datastore_id["\']?\s*:\s*["\']?([a-zA-Z0-9_\-]+)'
            ],
            "output_schema": [
                r"\*\*Output Schema:\*\*\s*(.+)",
                r"Output Schema:\s*(.+)",
                r'output_schema["\']?\s*:\s*["\']?([a-zA-Z0-9_\-]+)'
            ],
            "category": [
                r"\*\*Category:\*\*\s*(.+)",
                r"Category:\s*(.+)",
                r'category["\']?\s*:\s*["\']?([^\n"\'\r]+)'
            ],
            "skill_id": [
                r'skill_id["\']?\s*:\s*["\']?(SKILL_[A-Z0-9_]+)',
                r'skill_id["\']?\s*:\s*["\']?([a-zA-Z0-9_\-]+)'
            ],
            "agent_name": [
                r'agent_name["\']?\s*:\s*["\']?([a-zA-Z0-9_\-]+)'
            ],
            "title": [
                r'title["\']?\s*:\s*["\']?([^\n"\'\r]+)'
            ],
            "description": [
                r'description["\']?\s*:\s*["\']?([^\n"\'\r]+)'
            ]
        }

        for key, regex_list in patterns.items():
            for pattern in regex_list:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    metadata[key] = match.group(1).strip()
                    break

        return metadata