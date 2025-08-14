import uuid
from pydantic import BaseModel, Field
from typing import Any, Dict
from datetime import datetime, timezone

INITIAL_ANALYSIS_PRODUCED = "INITIAL_ANALYSIS_PRODUCED"
CREATIVE_SPARKS_PRODUCED = "CREATIVE_SPARKS_PRODUCED"
REVISION_COMPLETE = "REVISION_COMPLETE"
DEVILS_ADVOCATE_CRITIQUE_PRODUCED = "DEVILS_ADVOCATE_CRITIQUE_PRODUCED"
SYNTHESIS_COMPLETE = "SYNTHESIS_COMPLETE"
QA_FEEDBACK_PRODUCED = "QA_FEEDBACK_PRODUCED"


class Event(BaseModel):
    """
    The standard unit of the Reasoning Ledger.
    Represents a single, immutable action taken by an agent or system component.
    """
    run_id: str
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str
    source: str 
    payload: Dict[str, Any]