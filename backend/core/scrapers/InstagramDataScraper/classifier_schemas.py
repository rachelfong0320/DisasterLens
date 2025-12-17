from typing import Literal
from pydantic import BaseModel, Field

class ClassificationOutput(BaseModel):
    reasoning: str = Field(description="Step-by-step analysis of the posts's content, tone, and specificity.")
    check_label: Literal["MISINFORMATION", "AUTHENTIC", "UNCERTAIN"] = Field(description="The final classification label.")
    justification: str = Field(description="A brief, one-sentence summary justification.")
    confidence_score: float = Field(description="A float score between 0.0 and 1.0 representing confidence.")