import re
from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage

from src.models import RubricScore, InterviewQuestion, QuestionMetadata


class EvaluationAgent:
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm

    def evaluate_response(
        self, response: str, question: InterviewQuestion
    ) -> RubricScore:
        correctness_score = self._evaluate_correctness(response, question.metadata)
        clarity_score = self._evaluate_explanation_clarity(response, question)
        specificity_score = self._evaluate_excel_specificity(response, question)

        problem_solving_score = None
        if question.metadata.topic == "scenarios":
            problem_solving_score = self._evaluate_problem_solving(response, question)

        evaluator_notes = self._generate_evaluator_notes(
            response, question, correctness_score, clarity_score, specificity_score
        )

        return RubricScore(
            correctness=correctness_score,
            explanation_clarity=clarity_score,
            excel_specificity=specificity_score,
            problem_solving=problem_solving_score,
            evaluator_notes=evaluator_notes,
        )

    def _evaluate_correctness(self, response: str, metadata: QuestionMetadata) -> int:
        if metadata.expected_formula:
            formula_score = self._check_formula_correctness(
                response, metadata.expected_formula
            )
        else:
            formula_score = 3

        concept_score = self._check_concept_coverage(
            response, metadata.expected_concepts
        )

        return min(5, max(1, int((formula_score + concept_score) / 2)))

    def _check_formula_correctness(self, response: str, expected_formula: str) -> int:
        response_upper = response.upper()
        expected_upper = expected_formula.upper()

        expected_function = expected_upper.split("(")[0].replace("=", "")

        if expected_function in response_upper:
            if "=" in response and "(" in response and ")" in response:
                return 5
            else:
                return 3
        else:
            return 1

    def _check_concept_coverage(
        self, response: str, expected_concepts: List[str]
    ) -> int:
        response_lower = response.lower()
        covered_concepts = 0

        for concept in expected_concepts:
            concept_words = concept.lower().split()
            if all(word in response_lower for word in concept_words):
                covered_concepts += 1

        coverage_ratio = covered_concepts / len(expected_concepts)

        if coverage_ratio >= 0.8:
            return 5
        elif coverage_ratio >= 0.6:
            return 4
        elif coverage_ratio >= 0.4:
            return 3
        elif coverage_ratio >= 0.2:
            return 2
        else:
            return 1

    def _evaluate_explanation_clarity(
        self, response: str, question: InterviewQuestion
    ) -> int:
        clarity_prompt = f"""
        Evaluate the clarity of this Excel explanation on a scale of 1-5:
        
        Question: {question.question_text}
        
        Response: {response}
        
        Scoring criteria:
        5 - Crystal clear, well-structured, easy to follow
        4 - Clear with minor issues
        3 - Somewhat clear but could be improved
        2 - Unclear in several areas
        1 - Very unclear or confusing
        
        Respond with only a number from 1-5.
        """

        messages = [
            SystemMessage(
                content="You are evaluating the clarity of Excel explanations."
            ),
            HumanMessage(content=clarity_prompt),
        ]

        try:
            response_content = self.llm.invoke(messages).content
            score = int(re.search(r"[1-5]", response_content).group())
            return score
        except:
            return 3

    def _evaluate_excel_specificity(
        self, response: str, question: InterviewQuestion
    ) -> int:
        specificity_prompt = f"""
        Evaluate how Excel-specific this response is on a scale of 1-5:
        
        Question: {question.question_text}
        
        Response: {response}
        
        Scoring criteria:
        5 - Highly Excel-specific with proper function names, syntax, and Excel terminology
        4 - Mostly Excel-specific with some generic elements
        3 - Mix of Excel-specific and generic advice
        2 - Mostly generic with minimal Excel specifics
        1 - Generic response that could apply to any spreadsheet software
        
        Respond with only a number from 1-5.
        """

        messages = [
            SystemMessage(content="You are evaluating Excel specificity in responses."),
            HumanMessage(content=specificity_prompt),
        ]

        try:
            response_content = self.llm.invoke(messages).content
            score = int(re.search(r"[1-5]", response_content).group())
            return score
        except:
            return 3

    def _evaluate_problem_solving(
        self, response: str, question: InterviewQuestion
    ) -> int:
        problem_solving_prompt = f"""
        Evaluate the problem-solving approach in this response on a scale of 1-5:
        
        Scenario: {question.question_text}
        
        Response: {response}
        
        Scoring criteria:
        5 - Systematic approach, considers multiple aspects, shows strategic thinking
        4 - Good approach with clear steps and reasoning
        3 - Basic approach that addresses the main requirements
        2 - Limited approach, misses some key aspects
        1 - Poor approach, doesn't address the problem effectively
        
        Respond with only a number from 1-5.
        """

        messages = [
            SystemMessage(
                content="You are evaluating problem-solving approaches in Excel scenarios."
            ),
            HumanMessage(content=problem_solving_prompt),
        ]

        try:
            response_content = self.llm.invoke(messages).content
            score = int(re.search(r"[1-5]", response_content).group())
            return score
        except:
            return 3

    def _generate_evaluator_notes(
        self,
        response: str,
        question: InterviewQuestion,
        correctness: int,
        clarity: int,
        specificity: int,
    ) -> str:
        notes_prompt = f"""
        Generate brief evaluator notes for this Excel interview response:
        
        Question: {question.question_text}
        Response: {response}
        
        Scores: Correctness={correctness}, Clarity={clarity}, Specificity={specificity}
        
        Provide 2-3 sentences highlighting:
        1. Key strengths in the response
        2. Main areas for improvement
        
        Keep it constructive and specific.
        """

        messages = [
            SystemMessage(
                content="You are generating evaluator notes for Excel interview responses."
            ),
            HumanMessage(content=notes_prompt),
        ]

        try:
            return self.llm.invoke(messages).content
        except:
            return f"Response evaluated with scores: Correctness={correctness}, Clarity={clarity}, Specificity={specificity}"
