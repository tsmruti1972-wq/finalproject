from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    task_type: str = Field(..., description="One of: variance_explanation, executive_narrative, assumption_risk_check")
    user_message: str = Field(..., min_length=1)
    context_assumptions: str = ""
    csv_content: list[dict[str, Any]] = Field(default_factory=list)


class RetrievedDoc(BaseModel):
    id: str
    title: str
    snippet: str
    score: float


class ChatResponse(BaseModel):
    response_text: str
    retrieved_docs: list[RetrievedDoc]
