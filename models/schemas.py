# models/schemas.py
from enum import Enum
from typing import Type, Any
from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ChatMessage(BaseModel):
    sender: str
    content: str
    timestamp: float


class IntakeSessionState(BaseModel):
    session_id: str
    user_id: str = "anonymous"
    current_turn: int = 0
    status: str = SessionStatus.IN_PROGRESS.value
    conversation_history: list[ChatMessage] = Field(default_factory=list)
    collected_fields: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------
# Skill Specification Schema Contract
# ---------------------------------------------------------

# The contract for authoring skills; all skills must adhere to this contract
class AisleSkill(BaseModel):
    """Authoring contract for enterprise skills before draft ingestion."""
    skill_id: str = Field(description="Unique string identifier for the skill.")
    agent_name: str = Field(description="Name of the persona or agent executing the skill.")
    title: str = Field(description="Human-readable title of the skill.")
    description: str = Field(description="High-level goal and operational behavior summary.")
    routing_signals: list[str] = Field(default_factory=list, description="Keywords and trigger phrases for routing.")
    tool_names: list[str] = Field(default_factory=list, description="Bound tools and API integrations.")
    category: str = Field(default="Decision Operations", description="Operational domain category.")
    target_datastore_id: str = Field(default="decision-ops-ds", description="Target Vertex AI Search Data Store ID.")
    output_schema: str = Field(default="InnovationIntakeResult", description="Pydantic response schema class name.")
    active_version: str = Field(default="1.0.0", description="Semantic version string.")
    instructions_markdown: str = Field(default="", description="The core markdown prompt instructions.")

    def to_yaml_markdown(self) -> str:
        """Serializes the AisleSkill model into standard YAML frontmatter + markdown body."""
        signals_formatted = "\n".join([f'  - "{s}"' for s in self.routing_signals])
        tools_formatted = "\n".join([f'  - "{t}"' for t in self.tool_names])

        return f"""---
skill_id: "{self.skill_id}"
agent_name: "{self.agent_name}"
title: "{self.title}"
description: "{self.description}"
active_version: "{self.active_version}"
category: "{self.category}"
target_datastore_id: "{self.target_datastore_id}"
output_schema: "{self.output_schema}"
routing_signals:
{signals_formatted if signals_formatted else "  []"}
tool_names:
{tools_formatted if tools_formatted else "  []"}
status: "DRAFT"
---

{self.instructions_markdown.strip()}
"""


class TaskPayload(BaseModel):
    """Immutable task payload dispatched to workers via Cloud Tasks."""
    skill_id: str
    generation_id: str
    target_datastore_id: str
    output_schema: str = "InnovationIntakeResult"
    skill_gcs_uri: str
    intake_content: str  # Inline sanitized markdown content


# ---------------------------------------------------------
# Worker Output Models
# ---------------------------------------------------------
# Abstract schema that establishes the structure of what the final output should be from the worker agent
class BaseWorkerResult(BaseModel):
    summary: str = Field(description="High-level executive summary of the evaluation.")
    markdown_report: str = Field(description="Detailed human-readable markdown report including matrices and action items.")

# Placeholder schema representing the output for another use-case i.e security risk review.
class SecurityAuditResult(BaseWorkerResult):
    risk_score: float = Field(description="Severity score from 0.0 to 10.0.")
    risk_category: str = Field(description="Risk category (Critical, High, Medium, Low).")
    compliance_flags: list[str] = Field(default_factory=list, description="Identified compliance violations.")

# The output schema defined for the Innovation Intake Process.
class InnovationIntakeResult(BaseWorkerResult):
    idea_score: float = Field(
        description="Calculated evaluation score (e.g., 0.0-10.0 risk score, 0-100% compliance score, or health score)."
    )
    score_classification: str = Field(
        description="Qualitative label for the score (e.g., 'APPROVED / LOW RISK', 'HIGH RISK', 'RETURNED (FAIL)', 'RECEIVED (PASS)')."
    )
    recommendation_details: list[str] = Field(
        default_factory=list,
        description="Itemized list of prescriptive remediation recommendations and structured decision pathways."
    )
    compliance_flags: list[str] = Field(
        default_factory=list,
        description="Specific policy gaps or rule violations identified."
    )


class GenericWorkerResult(BaseWorkerResult):
    key_findings: list[str] = Field(default_factory=list, description="Key operational findings.")


# ---------------------------------------------------------
# Centralized Schema Registry Factory
# ---------------------------------------------------------

# Registry to host the different types of output schemas produced by the worker agents.
SCHEMA_REGISTRY: dict[str, Type[BaseWorkerResult]] = {
    "InnovationIntakeResult": InnovationIntakeResult,
    "SecurityAuditResult": SecurityAuditResult,
    "GenericWorkerResult": GenericWorkerResult,
    "default": InnovationIntakeResult
}

def get_schema_by_name(schema_name: str | None) -> Type[BaseWorkerResult]:
    """Resolves a string schema name passed in TaskPayload to a concrete Pydantic class."""
    if not schema_name:
        return SCHEMA_REGISTRY["default"]
    return SCHEMA_REGISTRY.get(schema_name, SCHEMA_REGISTRY["default"])