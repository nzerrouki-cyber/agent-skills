from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum

# Current status of Conversational Intake Session.
class SessionStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

# Defines the user and messages sent back-and-forth between the user and IntakeAgent.
class ChatMessage(BaseModel):
    sender: str  # "user" or "agent"
    content: str
    timestamp: float

# The conversation payload after each exchange.
class IntakeSessionState(BaseModel):
    session_id: str
    user_id: str
    status: SessionStatus = SessionStatus.IN_PROGRESS
    current_turn: int = 0
    conversation_history: List[ChatMessage] = []
    collected_fields: Dict[str, Any] = Field(default_factory=dict)
    category: Optional[str] = None
    target_datastore_id: Optional[str] = None