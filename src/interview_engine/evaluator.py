import json
import hashlib
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from src.interview_engine.models import Question, ResponseRecord, InterviewState

logger = logging.getLogger(__name__)


class Evaluator(ABC):
    @abstractmethod
    def evaluate(
        self, question: Question, answer_text: str, state: InterviewState
    ) -> ResponseRecord:
        pass


class LLMEvaluator(Evaluator):
    def __init__(self, model_name: str = "gemini-2.5-flash", temperature: float = 0.1):
        self.model_name = model_name
        self.temperature = temperature
        self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=temperature)

        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", self._get_system_prompt()),
                ("human", self._get_evaluation_prompt()),
            ]
        )

        self.parser = JsonOutputParser()
        self.chain = self.prompt_template | self.llm | self.parser

    def _get_system_prompt(self) -> str:
        return """You are an objective technical interviewer evaluator. Given the question, the candidate's answer, and the rubric, return a **strict JSON** with the schema below. Do NOT output any additional commentary or explanation outside the JSON.

Return JSON following this exact schema:
{{
  "scores": {{
    "correctness": 0.0,
    "design": 0.0,
    "communication": 0.0,
    "production": 0.0,
    "overall": 0.0
  }},
  "rationale": "One-sentence justification (<=40 words).",
  "advice": ["One actionable suggestion per weak area."],
  "evidence": ["short quote from candidate answer (<=20 words)"]
}}"""

    def _get_evaluation_prompt(self) -> str:
        return """QUESTION:
{question_text}

CANDIDATE ANSWER:
{answer_text}

RUBRIC:
- correctness (0-5): Is the answer factually correct and technically accurate?
- design (0-5): Shows architecture understanding, tradeoffs, and system thinking?
- communication (0-5): Clarity, structure, examples, and explanation quality.
- production (0-5): Code quality, scalability, maintainability considerations.

Calculate overall as weighted average: correctness*0.4 + design*0.3 + communication*0.2 + production*0.1

Return JSON following the schema exactly."""

    def _get_evaluator_id(self) -> str:
        prompt_hash = hashlib.md5(
            (self._get_system_prompt() + self._get_evaluation_prompt()).encode()
        ).hexdigest()[:8]
        return f"{self.model_name}-{prompt_hash}"

    def evaluate(
        self, question: Question, answer_text: str, state: InterviewState
    ) -> ResponseRecord:
        try:
            result = self.chain.invoke(
                {"question_text": question.text, "answer_text": answer_text}
            )

            scores = result.get("scores", {})
            if "overall" not in scores:
                scores["overall"] = self._calculate_overall_score(scores)

            return ResponseRecord(
                question_id=question.id,
                question_text=question.text,
                answer_text=answer_text,
                timestamp=datetime.utcnow(),
                evaluator_id=self._get_evaluator_id(),
                scores=scores,
                rationale=result.get("rationale", ""),
                deterministic_results={},
            )

        except Exception as e:
            logger.error(f"LLM evaluation failed: {e}")
            return self._create_fallback_response(question, answer_text, str(e))

    def _calculate_overall_score(self, scores: Dict[str, float]) -> float:
        weights = {
            "correctness": 0.4,
            "design": 0.3,
            "communication": 0.2,
            "production": 0.1,
        }

        total = 0.0
        for dimension, weight in weights.items():
            total += scores.get(dimension, 0.0) * weight

        return total

    def _create_fallback_response(
        self, question: Question, answer_text: str, error: str
    ) -> ResponseRecord:
        return ResponseRecord(
            question_id=question.id,
            question_text=question.text,
            answer_text=answer_text,
            timestamp=datetime.utcnow(),
            evaluator_id=f"{self._get_evaluator_id()}-fallback",
            scores={
                "correctness": 2.5,
                "design": 2.5,
                "communication": 2.5,
                "production": 2.5,
                "overall": 2.5,
            },
            rationale=f"Evaluation failed, using fallback scores. Error: {error}",
            deterministic_results={"error": error},
        )


class MockEvaluator(Evaluator):
    def __init__(self):
        import random

        self.random = random

    def evaluate(
        self, question: Question, answer_text: str, state: InterviewState
    ) -> ResponseRecord:
        scores = {
            "correctness": float(self.random.randint(3, 5)),
            "design": float(self.random.randint(2, 5)),
            "communication": float(self.random.randint(2, 5)),
            "production": float(self.random.randint(2, 4)),
        }
        scores["overall"] = (
            scores["correctness"] * 0.4
            + scores["design"] * 0.3
            + scores["communication"] * 0.2
            + scores["production"] * 0.1
        )

        return ResponseRecord(
            question_id=question.id,
            question_text=question.text,
            answer_text=answer_text,
            timestamp=datetime.utcnow(),
            evaluator_id="mock-v1",
            scores=scores,
            rationale="Mock evaluation: concise and mostly correct.",
            deterministic_results={},
        )
