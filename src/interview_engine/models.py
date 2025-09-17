from typing import List, Dict, Optional

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal
from pydantic import BaseModel, Field
from datetime import datetime

Score = Dict[str, float]


class Question(BaseModel):
    id: str
    text: str
    type: Literal["qa", "scenario", "behavioral", "coding"] = "qa"
    metadata: Dict[str, str] = Field(default_factory=dict)


class ResponseRecord(BaseModel):
    question_id: str
    question_text: str
    answer_text: str
    timestamp: datetime
    evaluator_id: Optional[str] = None
    scores: Optional[Score] = None
    rationale: Optional[str] = None
    deterministic_results: Optional[Dict[str, str]] = None


class InterviewState(BaseModel):
    session_id: str
    phase: Literal["intro", "qa", "scenario", "reflection", "closing"]
    q_index: int = 0
    difficulty_level: int = 1
    questions: List[Question] = Field(default_factory=list)
    responses: List[ResponseRecord] = Field(default_factory=list)
    start_time: datetime
    end_time: Optional[datetime] = None
    feedback_report: Optional[Dict] = None
    meta: Dict[str, str] = Field(default_factory=dict)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
