import statistics
from typing import Dict, List, Any
import datetime

from src.interview_engine.models import InterviewState, ResponseRecord


class Reporter:
    def __init__(self):
        self.score_dimensions = ["correctness", "design", "communication", "production"]
        self.weights = {
            "correctness": 0.4,
            "design": 0.3,
            "communication": 0.2,
            "production": 0.1,
        }

    def generate_report(self, state: InterviewState) -> Dict[str, Any]:
        if not state.responses:
            return {
                "message": "No responses to evaluate",
                "session_id": state.session_id,
                "timestamp": datetime.datetime.now(
                    tz=datetime.timezone.utc
                ).isoformat(),
            }

        scores_summary = self._calculate_scores_summary(state.responses)
        strengths_weaknesses = self._identify_strengths_weaknesses(scores_summary)
        advice = self._generate_advice(state.responses)

        report = {
            "session_id": state.session_id,
            "timestamp": datetime.datetime.now(tz=datetime.timezone.utc),
            "duration_minutes": self._calculate_duration(state),
            "questions_answered": len(state.responses),
            "scores": scores_summary,
            "overall_score": scores_summary.get("overall", {}).get("mean", 0),
            "overall_score_normalized": min(
                100, max(0, scores_summary.get("overall", {}).get("mean", 0) * 20)
            ),
            "strengths": strengths_weaknesses["strengths"],
            "areas_for_improvement": strengths_weaknesses["weaknesses"],
            "actionable_advice": advice,
            "detailed_responses": self._format_detailed_responses(state.responses),
            "meta": state.meta,
        }

        return report

    def _calculate_scores_summary(
        self, responses: List[ResponseRecord]
    ) -> Dict[str, Dict[str, float]]:
        scores_by_dimension = {dim: [] for dim in self.score_dimensions + ["overall"]}

        for response in responses:
            if response.scores:
                for dim in self.score_dimensions + ["overall"]:
                    if dim in response.scores:
                        scores_by_dimension[dim].append(response.scores[dim])

        summary = {}
        for dim, scores in scores_by_dimension.items():
            if scores:
                summary[dim] = {
                    "mean": statistics.mean(scores),
                    "median": statistics.median(scores),
                    "min": min(scores),
                    "max": max(scores),
                    "count": len(scores),
                }
            else:
                summary[dim] = {
                    "mean": 0.0,
                    "median": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                    "count": 0,
                }

        return summary

    def _identify_strengths_weaknesses(
        self, scores_summary: Dict[str, Dict[str, float]]
    ) -> Dict[str, List[str]]:
        strengths = []
        weaknesses = []

        for dim in self.score_dimensions:
            if dim in scores_summary:
                mean_score = scores_summary[dim]["mean"]
                if mean_score >= 4.0:
                    strengths.append(self._dimension_to_strength(dim, mean_score))
                elif mean_score < 3.0:
                    weaknesses.append(self._dimension_to_weakness(dim, mean_score))

        overall_score = scores_summary.get("overall", {}).get("mean", 0)
        if overall_score >= 4.0:
            strengths.append(
                f"Strong overall performance (score: {overall_score:.1f}/5)"
            )
        elif overall_score < 3.0:
            weaknesses.append(
                f"Overall performance needs improvement (score: {overall_score:.1f}/5)"
            )

        return {"strengths": strengths, "weaknesses": weaknesses}

    def _dimension_to_strength(self, dimension: str, score: float) -> str:
        templates = {
            "correctness": f"Demonstrates strong technical accuracy (score: {score:.1f}/5)",
            "design": f"Shows excellent system design thinking (score: {score:.1f}/5)",
            "communication": f"Communicates clearly and effectively (score: {score:.1f}/5)",
            "production": f"Understands production-ready considerations (score: {score:.1f}/5)",
        }
        return templates.get(
            dimension, f"Strong {dimension} skills (score: {score:.1f}/5)"
        )

    def _dimension_to_weakness(self, dimension: str, score: float) -> str:
        templates = {
            "correctness": f"Technical accuracy needs improvement (score: {score:.1f}/5)",
            "design": f"System design thinking could be stronger (score: {score:.1f}/5)",
            "communication": f"Communication clarity needs work (score: {score:.1f}/5)",
            "production": f"Production considerations need more attention (score: {score:.1f}/5)",
        }
        return templates.get(
            dimension, f"{dimension.title()} needs improvement (score: {score:.1f}/5)"
        )

    def _generate_advice(self, responses: List[ResponseRecord]) -> List[str]:
        advice = []
        advice_seen = set()

        for response in responses:
            if hasattr(response, "rationale") and response.rationale:
                continue

        for response in responses:
            if response.scores:
                for dim in self.score_dimensions:
                    if dim in response.scores and response.scores[dim] < 3.0:
                        suggestion = self._get_improvement_suggestion(dim)
                        if suggestion not in advice_seen:
                            advice.append(suggestion)
                            advice_seen.add(suggestion)

        if not advice:
            advice.append(
                "Continue practicing technical interviews to maintain strong performance"
            )

        return advice[:5]

    def _get_improvement_suggestion(self, dimension: str) -> str:
        suggestions = {
            "correctness": "Review fundamental concepts and practice technical accuracy",
            "design": "Study system design patterns and practice architectural thinking",
            "communication": "Practice explaining technical concepts with clear examples",
            "production": "Learn about scalability, monitoring, and production best practices",
        }
        return suggestions.get(dimension, f"Focus on improving {dimension} skills")

    def _format_detailed_responses(
        self, responses: List[ResponseRecord]
    ) -> List[Dict[str, Any]]:
        detailed = []

        for i, response in enumerate(responses, 1):
            detail = {
                "question_number": i,
                "question": response.question_text,
                "answer_preview": response.answer_text[:200] + "..."
                if len(response.answer_text) > 200
                else response.answer_text,
                "scores": response.scores or {},
                "rationale": response.rationale or "No evaluation rationale provided",
                "timestamp": response.timestamp.isoformat()
                if response.timestamp
                else None,
            }
            detailed.append(detail)

        return detailed

    def _calculate_duration(self, state: InterviewState) -> float:
        if state.end_time and state.start_time:
            duration = state.end_time - state.start_time
            return duration.total_seconds() / 60
        return 0.0

    def format_text_report(self, report: Dict[str, Any]) -> str:
        lines = [
            "# Interview Feedback Report",
            f"Session ID: {report['session_id']}",
            f"Date: {report['timestamp']}",
            f"Duration: {report['duration_minutes']:.1f} minutes",
            f"Questions Answered: {report['questions_answered']}",
            "",
            f"## Overall Score: {report['overall_score_normalized']:.0f}/100",
            f"Raw Score: {report['overall_score']:.2f}/5.0",
            "",
        ]

        if report["strengths"]:
            lines.extend(["## Strengths", ""])
            for strength in report["strengths"]:
                lines.append(f"- {strength}")
            lines.append("")

        if report["areas_for_improvement"]:
            lines.extend(["## Areas for Improvement", ""])
            for weakness in report["areas_for_improvement"]:
                lines.append(f"- {weakness}")
            lines.append("")

        if report["actionable_advice"]:
            lines.extend(["## Actionable Advice", ""])
            for advice in report["actionable_advice"]:
                lines.append(f"- {advice}")
            lines.append("")

        lines.extend(["## Score Breakdown", ""])

        for dim in ["correctness", "design", "communication", "production"]:
            if dim in report["scores"]:
                score = report["scores"][dim]["mean"]
                lines.append(f"- {dim.title()}: {score:.1f}/5.0")

        return "\n".join(lines)
