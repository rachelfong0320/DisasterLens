from typing import Literal
from pydantic import BaseModel, Field

# FR-019: The eight required disaster categories + 'none'
DisasterType = Literal[
    "flood", 
    "landslide", 
    "storm", 
    "haze", 
    "forest fire", 
    "earthquake", 
    "sinkhole", 
    "tsunami",
    "none"
]

class IncidentClassificationOutput(BaseModel):
    """Schema for the LLM's structured incident classification output."""
    
    # FR-021: Classification label
    classification_type: DisasterType = Field(
        ..., 
        description="The primary disaster type for the post, chosen from the predefined list. Use 'none' if irrelevant."
    )
    # Confidence score 0.0-1.0
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for the classification (0.0 to 1.0)."
    )