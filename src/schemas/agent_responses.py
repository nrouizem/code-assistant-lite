from pydantic import BaseModel, Field
from typing import List

class ArchitectRevision(BaseModel):
    analysis_text: str = Field(description="The full, revised analysis in markdown format.")
    confidence_score: int = Field(description="An integer from 1 to 10 for confidence.", default=1)

class AnalogyAbstractions(BaseModel):
    analogies: List[str] = Field(description="A list of analogies from other domains.", default_factory=list)
    abstractions: List[str] = Field(description="A list of formal problem abstractions.", default_factory=list)