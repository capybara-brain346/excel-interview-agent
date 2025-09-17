from typing import Dict, List, Optional, TypedDict, Literal
from pydantic import BaseModel


class RubricScore(BaseModel):
    correctness: int
    explanation_clarity: int
    excel_specificity: int
    problem_solving: Optional[int] = None
    evaluator_notes: str = ""


class QuestionMetadata(BaseModel):
    question_id: str
    difficulty: Literal["basic", "intermediate", "advanced"]
    topic: Literal["formulas", "pivot_tables", "data_cleaning", "charting", "scenarios"]
    expected_concepts: List[str]
    expected_formula: Optional[str] = None


class InterviewQuestion(BaseModel):
    metadata: QuestionMetadata
    question_text: str
    context: Optional[str] = None


class FeedbackReport(BaseModel):
    strengths: List[str]
    weaknesses: List[str]
    next_steps: List[str]
    readiness_score: Optional[int] = None
    overall_summary: str


class AutomationState(TypedDict):
    phase: Literal["intro", "qa", "scenario", "reflection", "closing"]
    q_index: int
    responses: List[str]
    scores: List[RubricScore]
    reflection: Optional[str]
    current_question: Optional[InterviewQuestion]
    difficulty_level: Literal["basic", "intermediate", "advanced"]
    feedback_report: Optional[FeedbackReport]
    conversation_history: List[Dict[str, str]]
