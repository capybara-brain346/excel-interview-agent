from typing import List, Dict, Any
from statistics import mean
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage

from src.models import AutomationState, FeedbackReport, RubricScore


class FeedbackAgent:
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm

    def generate_feedback_report(self, state: AutomationState) -> FeedbackReport:
        scores = state["scores"]
        responses = state["responses"]
        reflection = state.get("reflection", "")

        strengths = self._identify_strengths(scores, responses)
        weaknesses = self._identify_weaknesses(scores, responses)
        next_steps = self._generate_next_steps(scores, weaknesses, reflection)
        readiness_score = self._calculate_readiness_score(scores)
        overall_summary = self._generate_overall_summary(
            scores, strengths, weaknesses, reflection
        )

        return FeedbackReport(
            strengths=strengths,
            weaknesses=weaknesses,
            next_steps=next_steps,
            readiness_score=readiness_score,
            overall_summary=overall_summary,
        )

    def _identify_strengths(
        self, scores: List[RubricScore], responses: List[str]
    ) -> List[str]:
        strengths = []

        if not scores:
            return ["Participated in the interview process"]

        avg_correctness = mean([score.correctness for score in scores])
        avg_clarity = mean([score.explanation_clarity for score in scores])
        avg_specificity = mean([score.excel_specificity for score in scores])

        if avg_correctness >= 4.0:
            strengths.append("Strong technical accuracy in Excel concepts and formulas")

        if avg_clarity >= 4.0:
            strengths.append("Clear and well-structured explanations")

        if avg_specificity >= 4.0:
            strengths.append(
                "Excellent use of Excel-specific terminology and functions"
            )

        high_scoring_areas = []
        for score in scores:
            if score.correctness >= 4:
                high_scoring_areas.append("formula correctness")
            if score.explanation_clarity >= 4:
                high_scoring_areas.append("communication")
            if score.excel_specificity >= 4:
                high_scoring_areas.append("Excel expertise")

        if high_scoring_areas:
            unique_areas = list(set(high_scoring_areas))
            if len(unique_areas) > 1:
                strengths.append(
                    f"Consistent performance across multiple areas: {', '.join(unique_areas)}"
                )

        if len(responses) > 0:
            avg_response_length = mean(
                [len(response.split()) for response in responses]
            )
            if avg_response_length > 50:
                strengths.append("Provided detailed and comprehensive answers")

        if not strengths:
            strengths.append(
                "Showed engagement and willingness to participate in the interview"
            )

        return strengths

    def _identify_weaknesses(
        self, scores: List[RubricScore], responses: List[str]
    ) -> List[str]:
        weaknesses = []

        if not scores:
            return ["Limited responses provided for evaluation"]

        avg_correctness = mean([score.correctness for score in scores])
        avg_clarity = mean([score.explanation_clarity for score in scores])
        avg_specificity = mean([score.excel_specificity for score in scores])

        if avg_correctness <= 2.5:
            weaknesses.append(
                "Technical accuracy needs improvement - focus on learning correct Excel formulas and functions"
            )

        if avg_clarity <= 2.5:
            weaknesses.append("Explanations could be clearer and more structured")

        if avg_specificity <= 2.5:
            weaknesses.append(
                "Responses were too generic - need more Excel-specific details and terminology"
            )

        low_scoring_areas = []
        for score in scores:
            if score.correctness <= 2:
                low_scoring_areas.append("formula accuracy")
            if score.explanation_clarity <= 2:
                low_scoring_areas.append("explanation clarity")
            if score.excel_specificity <= 2:
                low_scoring_areas.append("Excel specificity")

        if low_scoring_areas:
            unique_areas = list(set(low_scoring_areas))
            if len(unique_areas) > 1:
                weaknesses.append(
                    f"Multiple areas need attention: {', '.join(unique_areas)}"
                )

        problem_solving_scores = [
            score.problem_solving
            for score in scores
            if score.problem_solving is not None
        ]
        if problem_solving_scores and mean(problem_solving_scores) <= 2.5:
            weaknesses.append(
                "Problem-solving approach could be more systematic and comprehensive"
            )

        if len(responses) > 0:
            avg_response_length = mean(
                [len(response.split()) for response in responses]
            )
            if avg_response_length < 20:
                weaknesses.append(
                    "Responses were too brief - provide more detailed explanations"
                )

        return weaknesses

    def _generate_next_steps(
        self, scores: List[RubricScore], weaknesses: List[str], reflection: str
    ) -> List[str]:
        next_steps_prompt = f"""
        Based on the interview performance and identified weaknesses, generate 3-4 specific, actionable next steps for Excel skill development.
        
        Performance Summary:
        - Average Correctness: {mean([s.correctness for s in scores]) if scores else 0:.1f}/5
        - Average Clarity: {mean([s.explanation_clarity for s in scores]) if scores else 0:.1f}/5
        - Average Specificity: {mean([s.excel_specificity for s in scores]) if scores else 0:.1f}/5
        
        Identified Weaknesses:
        {chr(10).join(f"- {weakness}" for weakness in weaknesses)}
        
        Candidate Reflection: {reflection}
        
        Provide specific, actionable recommendations like:
        - Study specific Excel functions or features
        - Practice particular types of problems
        - Use specific learning resources
        - Focus on particular skills
        
        Format as a simple list without bullet points or numbers.
        """

        messages = [
            SystemMessage(
                content="You are providing personalized Excel learning recommendations."
            ),
            HumanMessage(content=next_steps_prompt),
        ]

        try:
            response = self.llm.invoke(messages).content
            next_steps = [
                step.strip().lstrip("- ").lstrip("• ").lstrip("* ")
                for step in response.split("\n")
                if step.strip()
            ]
            return [step for step in next_steps if len(step) > 10][:4]
        except:
            return [
                "Practice basic Excel formulas like SUM, AVERAGE, and COUNT",
                "Learn VLOOKUP and INDEX/MATCH functions for data lookup",
                "Explore pivot tables for data summarization",
                "Study Excel's data analysis and visualization features",
            ]

    def _calculate_readiness_score(self, scores: List[RubricScore]) -> int:
        if not scores:
            return 30

        avg_correctness = mean([score.correctness for score in scores])
        avg_clarity = mean([score.explanation_clarity for score in scores])
        avg_specificity = mean([score.excel_specificity for score in scores])

        overall_avg = (avg_correctness + avg_clarity + avg_specificity) / 3

        readiness_score = int((overall_avg / 5) * 100)

        return max(0, min(100, readiness_score))

    def _generate_overall_summary(
        self,
        scores: List[RubricScore],
        strengths: List[str],
        weaknesses: List[str],
        reflection: str,
    ) -> str:
        summary_prompt = f"""
        Generate a concise overall summary (2-3 sentences) of the candidate's Excel interview performance.
        
        Performance Data:
        - Number of questions answered: {len(scores)}
        - Average scores: Correctness={mean([s.correctness for s in scores]) if scores else 0:.1f}, Clarity={mean([s.explanation_clarity for s in scores]) if scores else 0:.1f}, Specificity={mean([s.excel_specificity for s in scores]) if scores else 0:.1f}
        
        Key Strengths: {", ".join(strengths[:2])}
        Key Weaknesses: {", ".join(weaknesses[:2])}
        
        Candidate's Self-Reflection: {reflection}
        
        Provide an encouraging but honest assessment that acknowledges both strengths and areas for growth.
        """

        messages = [
            SystemMessage(
                content="You are providing an overall interview performance summary."
            ),
            HumanMessage(content=summary_prompt),
        ]

        try:
            return self.llm.invoke(messages).content
        except:
            if scores:
                avg_score = (
                    mean(
                        [
                            s.correctness + s.explanation_clarity + s.excel_specificity
                            for s in scores
                        ]
                    )
                    / 3
                )
                if avg_score >= 4:
                    return "Strong performance with good technical knowledge and clear communication. Continue building on these solid foundations."
                elif avg_score >= 3:
                    return "Solid understanding of Excel basics with room for improvement in advanced concepts and explanation clarity."
                else:
                    return "Good effort in the interview. Focus on strengthening fundamental Excel skills and practicing clear explanations."
            else:
                return "Thank you for participating in the interview. Focus on building foundational Excel skills."
