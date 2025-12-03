# classifier_schemas.py
from typing import Literal
from pydantic import BaseModel, Field

# --- 1. Misinformation Schema ---
class ClassificationOutput(BaseModel):
    """Schema for the misinformation classification output."""
    reasoning: str = Field(description="Step-by-step analysis.")
    check_label: Literal["MISINFORMATION", "AUTHENTIC", "UNCERTAIN"] = Field(description="The final label.")
    justification: str = Field(description="Brief justification.")
    confidence_score: float = Field(description="Score between 0.0 and 1.0.")

# --- 2. Sentiment Schema ---
class SentimentOutput(BaseModel):
    """Schema for disaster sentiment classification."""
    reasoning: str = Field(description="Reasoning based on disaster urgency.")
    sentiment_label: Literal["Urgent", "Warning", "Informational"] = Field(
        description="Urgent: Life threatening. Warning: Caution needed. Informational: General news."
    )
    confidence_score: float = Field(description="Confidence level between 0.0 and 1.0.")