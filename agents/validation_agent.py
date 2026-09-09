# agents/validation_agent.py
import re
import hashlib
from pydantic import BaseModel, Field
from google.genai import types

from agents.base_agent import BaseAgent
from config.settings import settings

# Defines the security risk of a skill added to Drafts GCS.
class SecurityAuditVerdict(BaseModel):
    is_secure: bool = Field(description="True if prompt contains no prompt injection or security issues.")
    security_score: float = Field(description="Score from 0.0 to 10.0 assessing security risk.")
    violation_reasons: list[str] = Field(default_factory=list, description="List of identified security violations.")

# Defines skill payload after it has been validated and added to Production GCS.
class ValidationResult(BaseModel):
    passed: bool
    skill_id: str
    errors: list[str] = Field(default_factory=list)
    frontmatter: dict = Field(default_factory=dict)
    checksum: str = ""

class SkillValidationAgent(BaseAgent):
    """3-Stage audit pipeline agent for evaluating and promoting skill drafts adhering to AisleSkill."""

    def __init__(self):
        super().__init__()

    # Retrieves the validation agent's skill so that this agent can start verifying new incoming skills.
    async def _get_validator_system_instruction(self) -> str:
        """Retrieves promoted Skill Validation System Prompt directly from Production GCS / Redis."""
        prompt_content, _, _ = await self.get_promoted_skill_prompt("SKILL_VALIDATION")
        return prompt_content

    # Defines the fields that each skill requires; invalid otherwise.
    def _audit_structure(self, frontmatter: dict, body: str) -> list[str]:
        errors = []
        required_fields = [
            "skill_id", 
            "agent_name",
            "title",
            "active_version", 
            "target_datastore_id", 
            "category", 
            "output_schema"
        ]
        
        for field in required_fields:
            if field not in frontmatter or not frontmatter[field]:
                errors.append(f"Structural Violation: Missing required YAML header key '{field}'.")

        if len(body) < 50:
            errors.append("Structural Violation: Skill instruction body is too short (< 50 characters).")

        return errors

    # Audits the skill from a security perspective.
    async def _audit_security_gate(self, body: str) -> list[str]:
        errors = []
        prohibited_patterns = [
            r"ignore previous instructions",
            r"system override",
            r"exfiltrate",
            r"http://[^\s]+",
        ]
        for pattern in prohibited_patterns:
            if re.search(pattern, body, re.IGNORECASE):
                errors.append(f"Security Gate Violation: Found suspicious directive pattern '{pattern}'.")

        validator_system_instruction = await self._get_validator_system_instruction()
        user_prompt = f"CANDIDATE DRAFT SYSTEM INSTRUCTION TO AUDIT:\n{body}"

        try:
            response = await self.genai_client.aio.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=validator_system_instruction,
                    response_mime_type="application/json",
                    response_schema=SecurityAuditVerdict,
                    temperature=0.0
                )
            )
            if response.parsed is not None:
                verdict: SecurityAuditVerdict = response.parsed
                if not verdict.is_secure:
                    errors.extend([f"Security Gate Violation: {reason}" for reason in verdict.violation_reasons])
            else:
                errors.append("Security Gate Audit Failed: Received empty or unparseable evaluation response.")
        except Exception as e:
            errors.append(f"Security Gate Audit Failed to Execute: {str(e)}")

        return errors

    # Hashes the skill payload to confirm authenticity and integrity.
    def _cryptographic_sign_check(self, body: str) -> str:
        return hashlib.sha256(body.encode("utf-8")).hexdigest()

    # Validates the incoming skill and promotes it to Production if valid.
    async def run_audit_pipeline(self, event_payload: dict) -> ValidationResult:

        # Retrieve the new skill from the Drafts GCS
        bucket_name, blob_name = self.extract_gcs_event_data(event_payload)
        raw_content = await self.gcs_service.download_blob_as_text(bucket_name, blob_name)
        
        try:
            frontmatter, markdown_body = self.parse_yaml_frontmatter(raw_content)
        except Exception as e:
            return ValidationResult(passed=False, skill_id="UNKNOWN", errors=[str(e)])

        skill_id = frontmatter.get("skill_id", "UNKNOWN")

        errors = self._audit_structure(frontmatter, markdown_body)
        security_errors = await self._audit_security_gate(markdown_body)
        errors.extend(security_errors)

        checksum = self._cryptographic_sign_check(markdown_body)

        # Fails if the new skill failed the validation check
        if errors:
            return ValidationResult(passed=False, skill_id=skill_id, errors=errors, frontmatter=frontmatter)

        # Reference Production GCS 
        prod_bucket_parts = settings.SKILL_PROD_BUCKET.strip("/").split("/", 1)
        prod_bucket_name = prod_bucket_parts[0]
        prod_blob_name = f"{prod_bucket_parts[1]}/{skill_id}.md" if len(prod_bucket_parts) > 1 else f"{skill_id}.md"

        # Inject active status frontmatter header prior to production persistence
        active_markdown = self.inject_yaml_frontmatter(
            skill_id=skill_id,
            markdown_content=markdown_body,
            target_datastore_id=frontmatter.get("target_datastore_id"),
            category=frontmatter.get("category"),
            agent_name=frontmatter.get("agent_name", "generic_specialist"),
            title=frontmatter.get("title", skill_id),
            description=frontmatter.get("description", ""),
            routing_signals=frontmatter.get("routing_signals", []),
            tool_names=frontmatter.get("tool_names", []),
            output_schema=frontmatter.get("output_schema", "InnovationIntakeResult"),
            active_version=frontmatter.get("active_version", "1.0.0"),
            status="ACTIVE"
        )

        # Uploads the new skill to Production GCS, indicating that this is a valid skill to be used
        await self.gcs_service.upload_string(
            bucket_setting=prod_bucket_name,
            blob_name=prod_blob_name,
            content=active_markdown,
            content_type="text/markdown"
        )

        # Retrieve generation ID from copied/promoted production blob
        prod_uri = f"gs://{prod_bucket_name}/{prod_blob_name}"
        generation_id = "1"
        try:
            generation_id = await self.gcs_service.copy_and_promote_blob(
                source_bucket_setting=bucket_name,
                source_blob_name=blob_name,
                dest_bucket_setting=prod_bucket_name,
                dest_blob_name=prod_blob_name
            )
        except Exception:
            pass

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
            "generation_id": generation_id,
            "checksum": checksum,
            "status": "ACTIVE"
        }
        # Inserts the skill_id and generation_id of the newly validated skill in our Skill Index Registry
        await self.firestore.upsert_skill_registry_index(registry_payload)
        # Caches the skill as a key-value object for immediate retrieval by the worker agent
        await self.redis_cache.set_skill(skill_id, generation_id, active_markdown)

        return ValidationResult(
            passed=True,
            skill_id=skill_id,
            frontmatter=registry_payload,
            checksum=checksum
        )