import statistics
from typing import Dict, List, Any
import datetime
import os
import tempfile
import logging

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from src.interview_engine.models import InterviewState, ResponseRecord

logger = logging.getLogger(__name__)


class Reporter:
    def __init__(self, model_name: str = "gemini-2.5-flash", temperature: float = 0.3):
        self.score_dimensions = ["correctness", "design", "communication", "production"]
        self.weights = {
            "correctness": 0.4,
            "design": 0.3,
            "communication": 0.2,
            "production": 0.1,
        }

        # Initialize LLM for agent-based report generation
        self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=temperature)
        self.parser = JsonOutputParser()

        # Create report generation chain
        self.report_prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", self._get_report_generation_system_prompt()),
                ("human", self._get_report_generation_prompt()),
            ]
        )
        self.report_chain = self.report_prompt_template | self.llm | self.parser

    def _get_report_generation_system_prompt(self) -> str:
        return """
        <system_prompt>
        <role>
            <primary_function>Excel Skills Interview Report Generator</primary_function>
            <task>Generate comprehensive, constructive feedback reports for Excel skills interviews</task>
        </role>

        <expertise>
            <domain>Excel skills assessment and training</domain>
            <focus_areas>
                <area>Excel formulas and functions</area>
                <area>Data analysis and visualization</area>
                <area>PivotTables and advanced features</area>
                <area>Workflow optimization and best practices</area>
            </focus_areas>
        </expertise>

        <report_philosophy>
            <approach>constructive and growth-oriented</approach>
            <tone>encouraging yet honest</tone>
            <focus>actionable insights and specific improvement strategies</focus>
            <goal>help candidates develop Excel mastery through targeted feedback</goal>
        </report_philosophy>

        <output_requirements>
            <format>strict JSON only</format>
            <restrictions>
                <restriction>NO additional commentary outside JSON</restriction>
                <restriction>MUST follow exact schema provided</restriction>
                <restriction>All feedback must be specific to Excel skills</restriction>
            </restrictions>
            
            <json_schema>
            {{
                "enhanced_feedback": {{
                    "correctness": {{
                        "current_level": "Expert|Advanced|Intermediate|Developing|Beginner",
                        "specific_feedback": "Detailed analysis of Excel technical accuracy",
                        "improvement_strategies": ["Specific Excel-focused strategies"],
                        "resources": ["Excel learning resources"]
                    }},
                    "design": {{
                        "current_level": "Expert|Advanced|Intermediate|Developing|Beginner", 
                        "specific_feedback": "Analysis of Excel solution design thinking",
                        "improvement_strategies": ["Excel design improvement strategies"],
                        "resources": ["Excel design resources"]
                    }},
                    "communication": {{
                        "current_level": "Expert|Advanced|Intermediate|Developing|Beginner",
                        "specific_feedback": "Analysis of Excel explanation clarity",
                        "improvement_strategies": ["Excel communication strategies"],
                        "resources": ["Excel communication resources"]
                    }},
                    "production": {{
                        "current_level": "Expert|Advanced|Intermediate|Developing|Beginner",
                        "specific_feedback": "Analysis of real-world Excel application understanding",
                        "improvement_strategies": ["Excel production readiness strategies"],
                        "resources": ["Excel production resources"]
                    }}
                }},
                "learning_path": {{
                    "priority_focus": "dimension needing most attention",
                    "secondary_focus": "second priority dimension",
                    "timeline": "realistic improvement timeline",
                    "milestones": ["Specific Excel learning milestones"]
                }},
                "performance_trends": {{
                    "trend": "improving|declining|consistent|insufficient_data",
                    "description": "Analysis of performance progression during interview"
                }},
                "next_steps": ["Immediate actionable Excel improvement steps"],
                "report_type": "constructive_feedback"
            }}
            </json_schema>
        </output_requirements>

        <content_guidelines>
            <feedback_quality>
                <specificity>Reference specific Excel features, functions, or concepts</specificity>
                <actionability>Provide concrete steps the candidate can take</actionability>
                <encouragement>Highlight strengths while addressing improvement areas</encouragement>
                <context>Consider the candidate's demonstrated Excel knowledge level</context>
            </feedback_quality>
            
            <resource_selection>
                <criteria>Choose resources appropriate to candidate's current level</criteria>
                <variety>Mix of official documentation, tutorials, and practice resources</variety>
                <accessibility>Ensure resources are readily available and practical</accessibility>
            </resource_selection>
        </content_guidelines>
        </system_prompt>
        """

    def _get_report_generation_prompt(self) -> str:
        return """
        Generate a comprehensive constructive feedback report for this Excel skills interview.

        <interview_data>
        <session_info>
        Session ID: {session_id}
        Duration: {duration_minutes} minutes
        Questions Answered: {questions_answered}
        </session_info>

        <performance_scores>
        Overall Score: {overall_score:.2f}/5.0 ({overall_score_normalized:.0f}/100)
        Correctness: {correctness_score:.2f}/5.0
        Design: {design_score:.2f}/5.0  
        Communication: {communication_score:.2f}/5.0
        Production: {production_score:.2f}/5.0
        </performance_scores>

        <detailed_responses>
        {detailed_responses}
        </detailed_responses>
        </interview_data>

        <analysis_requirements>
        1. Analyze the candidate's Excel knowledge across all four dimensions
        2. Identify specific strengths and areas for improvement
        3. Consider the progression of performance throughout the interview
        4. Generate personalized learning recommendations based on demonstrated skills
        5. Provide actionable next steps appropriate to the candidate's level
        6. Ensure all feedback is constructive, specific, and Excel-focused
        </analysis_requirements>

        Generate the JSON report following the exact schema provided in the system prompt.
        """

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
        """Generate a clean, readable report from the JSON data"""

        lines = [
            "# 📊 Excel Skills Interview Report",
            "",
            f"**Session ID:** {report.get('session_id', 'N/A')}",
            f"**Date:** {str(report.get('timestamp', ''))[:19]}",
            f"**Duration:** {report.get('duration_minutes', 0):.1f} minutes",
            f"**Questions Answered:** {report.get('questions_answered', 0)}",
            "",
            f"## 🎯 Overall Score: {report.get('overall_score_normalized', 0):.0f}/100",
            f"*Raw Score: {report.get('overall_score', 0):.2f}/5.0*",
            "",
        ]

        scores = report.get("scores", {})
        if scores:
            lines.extend(["## 📊 Score Breakdown", ""])

            for dimension in ["correctness", "design", "communication", "production"]:
                if dimension in scores:
                    score_data = scores[dimension]
                    mean_score = score_data.get("mean", 0)
                    lines.append(f"**{dimension.title()}:** {mean_score:.1f}/5.0")
            lines.append("")

        strengths = report.get("strengths", [])
        if strengths:
            lines.extend(["## ✅ Strengths", ""])
            for strength in strengths:
                lines.append(f"• {strength}")
            lines.append("")

        areas_for_improvement = report.get("areas_for_improvement", [])
        if areas_for_improvement:
            lines.extend(["## 🎯 Areas for Improvement", ""])
            for area in areas_for_improvement:
                lines.append(f"• {area}")
            lines.append("")

        advice = report.get("actionable_advice", [])
        if advice:
            lines.extend(["## 💡 Actionable Advice", ""])
            for item in advice:
                lines.append(f"• {item}")
            lines.append("")

        detailed_responses = report.get("detailed_responses", [])
        if detailed_responses:
            lines.extend(["## 📝 Question Summary", ""])

            for response in detailed_responses:
                q_num = response.get("question_number", "?")
                overall_score = response.get("scores", {}).get("overall", 0)
                lines.append(f"**Question {q_num}** (Score: {overall_score:.1f}/5.0)")
                lines.append(f"*Answer:* {response.get('answer_preview', 'No answer')}")

                rationale = response.get("rationale", "")
                if rationale and rationale != "No evaluation rationale provided":
                    lines.append(f"*Feedback:* {rationale}")
                lines.append("")

        lines.extend(["---", "", "*For detailed analysis, view the raw JSON report.*"])

        return "\n".join(lines)

    def get_json_report(self, report: Dict[str, Any]) -> str:
        """Return the raw JSON report as a formatted string"""
        import json

        return json.dumps(report, indent=2, default=str)

    def generate_constructive_feedback_report(
        self, state: InterviewState
    ) -> Dict[str, Any]:
        """Generate enhanced constructive feedback report using LLM agent"""
        # Generate base report with scores and basic data
        base_report = self.generate_report(state)

        if not state.responses:
            return base_report

        try:
            # Use LLM to generate constructive feedback
            agent_feedback = self._generate_agent_based_feedback(state, base_report)

            # Merge agent-generated feedback with base report
            base_report.update(agent_feedback)
            base_report["report_type"] = "constructive_feedback"

            return base_report

        except Exception as e:
            logger.error(f"Agent-based report generation failed: {e}")
            # Fallback to rule-based generation
            return self._generate_fallback_constructive_report(state, base_report)

    def _generate_agent_based_feedback(
        self, state: InterviewState, base_report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use LLM agent to generate constructive feedback"""
        try:
            # Prepare detailed responses for the prompt
            detailed_responses_text = self._format_responses_for_prompt(state.responses)

            # Calculate dimension scores
            scores_summary = base_report.get("scores", {})

            # Prepare prompt data
            prompt_data = {
                "session_id": state.session_id,
                "duration_minutes": base_report.get("duration_minutes", 0),
                "questions_answered": len(state.responses),
                "overall_score": base_report.get("overall_score", 0),
                "overall_score_normalized": base_report.get(
                    "overall_score_normalized", 0
                ),
                "correctness_score": scores_summary.get("correctness", {}).get(
                    "mean", 0
                ),
                "design_score": scores_summary.get("design", {}).get("mean", 0),
                "communication_score": scores_summary.get("communication", {}).get(
                    "mean", 0
                ),
                "production_score": scores_summary.get("production", {}).get("mean", 0),
                "detailed_responses": detailed_responses_text,
            }

            # Generate report using LLM
            agent_result = self.report_chain.invoke(prompt_data)

            return agent_result

        except Exception as e:
            logger.error(f"LLM report generation failed: {e}")
            raise

    def _format_responses_for_prompt(self, responses: List[ResponseRecord]) -> str:
        """Format interview responses for the LLM prompt"""
        formatted_responses = []

        for i, response in enumerate(responses, 1):
            response_text = f"""
            <response_{i}>
            <question>{response.question_text}</question>
            <answer>{response.answer_text}</answer>
            <scores>
                Correctness: {response.scores.get("correctness", 0):.1f}/5.0
                Design: {response.scores.get("design", 0):.1f}/5.0
                Communication: {response.scores.get("communication", 0):.1f}/5.0
                Production: {response.scores.get("production", 0):.1f}/5.0
                Overall: {response.scores.get("overall", 0):.1f}/5.0
            </scores>
            <evaluator_feedback>{response.rationale}</evaluator_feedback>
            </response_{i}>
            """
            formatted_responses.append(response_text.strip())

        return "\n\n".join(formatted_responses)

    def _generate_fallback_constructive_report(
        self, state: InterviewState, base_report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback to rule-based report generation if LLM fails"""
        logger.info("Using fallback rule-based report generation")

        enhanced_feedback = self._generate_enhanced_feedback(state.responses)
        learning_path = self._generate_learning_path(state.responses)
        performance_trends = self._analyze_performance_trends(state.responses)
        next_steps = self._generate_next_steps(
            state.responses, base_report.get("overall_score", 0)
        )

        base_report.update(
            {
                "enhanced_feedback": enhanced_feedback,
                "learning_path": learning_path,
                "performance_trends": performance_trends,
                "next_steps": next_steps,
                "report_type": "constructive_feedback",
                "generation_method": "fallback_rule_based",
            }
        )

        return base_report

    def _generate_enhanced_feedback(
        self, responses: List[ResponseRecord]
    ) -> Dict[str, Any]:
        """Generate detailed constructive feedback for each dimension"""
        feedback = {}

        for dimension in self.score_dimensions:
            scores = [
                r.scores.get(dimension, 0)
                for r in responses
                if r.scores and dimension in r.scores
            ]
            if not scores:
                continue

            avg_score = statistics.mean(scores)
            feedback[dimension] = {
                "current_level": self._get_skill_level(avg_score),
                "specific_feedback": self._get_specific_feedback(
                    dimension, avg_score, responses
                ),
                "improvement_strategies": self._get_improvement_strategies(
                    dimension, avg_score
                ),
                "resources": self._get_learning_resources(dimension),
            }

        return feedback

    def _get_skill_level(self, score: float) -> str:
        """Convert numeric score to skill level description"""
        if score >= 4.5:
            return "Expert"
        elif score >= 4.0:
            return "Advanced"
        elif score >= 3.0:
            return "Intermediate"
        elif score >= 2.0:
            return "Developing"
        else:
            return "Beginner"

    def _get_specific_feedback(
        self, dimension: str, avg_score: float, responses: List[ResponseRecord]
    ) -> str:
        """Generate specific feedback based on dimension and performance"""
        feedback_templates = {
            "correctness": {
                "high": "Your technical solutions demonstrate strong accuracy and understanding of Excel fundamentals. You consistently provide correct formulas and approaches.",
                "medium": "You show good grasp of Excel concepts but occasionally miss nuances in complex scenarios. Focus on edge cases and formula optimization.",
                "low": "There are opportunities to strengthen your Excel technical foundation. Review basic functions, formula syntax, and common Excel operations.",
            },
            "design": {
                "high": "Excellent approach to structuring Excel solutions. You think systematically about data organization and workflow efficiency.",
                "medium": "Good design thinking with room for improvement in considering scalability and maintainability of Excel solutions.",
                "low": "Focus on developing systematic approaches to Excel problem-solving. Consider data structure, user experience, and solution maintainability.",
            },
            "communication": {
                "high": "You explain Excel concepts clearly and provide helpful context for your solutions. Your communication enhances understanding.",
                "medium": "Generally clear communication with opportunities to be more specific about Excel terminology and step-by-step processes.",
                "low": "Work on explaining Excel solutions more clearly. Use specific terminology and break down complex processes into steps.",
            },
            "production": {
                "high": "Strong awareness of real-world Excel implementation challenges. You consider error handling, user experience, and maintainability.",
                "medium": "Good understanding of practical Excel considerations with room to think more about scalability and robustness.",
                "low": "Develop awareness of how Excel solutions work in practice. Consider error handling, data validation, and user-friendly design.",
            },
        }

        level = "high" if avg_score >= 4.0 else "medium" if avg_score >= 3.0 else "low"
        return feedback_templates.get(dimension, {}).get(
            level, f"Continue developing your {dimension} skills."
        )

    def _get_improvement_strategies(
        self, dimension: str, avg_score: float
    ) -> List[str]:
        """Get specific improvement strategies for each dimension"""
        strategies = {
            "correctness": [
                "Practice Excel functions daily with increasingly complex scenarios",
                "Review Excel documentation for advanced function usage",
                "Test formulas with edge cases and unusual data",
                "Use Excel's formula auditing tools to understand formula logic",
            ],
            "design": [
                "Study well-designed Excel templates and analyze their structure",
                "Practice organizing data with proper headers, formatting, and layout",
                "Learn about Excel table features and named ranges for better organization",
                "Consider user workflow when designing Excel solutions",
            ],
            "communication": [
                "Practice explaining Excel solutions to non-technical users",
                "Use comments and documentation within Excel files",
                "Create step-by-step guides for complex Excel processes",
                "Learn Excel terminology to communicate more precisely",
            ],
            "production": [
                "Learn about Excel security features and data protection",
                "Practice error handling with IFERROR and data validation",
                "Study Excel performance optimization techniques",
                "Consider version control and collaboration features in Excel",
            ],
        }

        all_strategies = strategies.get(dimension, [])
        if avg_score >= 4.0:
            return all_strategies[:2]
        elif avg_score >= 3.0:
            return all_strategies[:3]
        else:
            return all_strategies

    def _get_learning_resources(self, dimension: str) -> List[str]:
        """Get learning resources for each dimension"""
        resources = {
            "correctness": [
                "Microsoft Excel Help & Training (official documentation)",
                "ExcelJet - Excel formulas and functions reference",
                "Excel University courses for structured learning",
            ],
            "design": [
                "Excel Dashboard School for design principles",
                "Microsoft Excel templates gallery for inspiration",
                "Excel Campus courses on professional Excel design",
            ],
            "communication": [
                "Excel documentation best practices guides",
                "Technical writing courses for clear explanations",
                "Excel user community forums for communication practice",
            ],
            "production": [
                "Microsoft Excel security and compliance documentation",
                "Excel VBA resources for automation and robustness",
                "Business analysis courses focusing on Excel implementations",
            ],
        }
        return resources.get(dimension, [])

    def _generate_learning_path(
        self, responses: List[ResponseRecord]
    ) -> Dict[str, Any]:
        """Generate a personalized learning path based on performance"""
        if not responses:
            return {}

        dimension_scores = {}
        for dimension in self.score_dimensions:
            scores = [
                r.scores.get(dimension, 0)
                for r in responses
                if r.scores and dimension in r.scores
            ]
            if scores:
                dimension_scores[dimension] = statistics.mean(scores)

        sorted_dimensions = sorted(dimension_scores.items(), key=lambda x: x[1])

        learning_path = {
            "priority_focus": sorted_dimensions[0][0]
            if sorted_dimensions
            else "correctness",
            "secondary_focus": sorted_dimensions[1][0]
            if len(sorted_dimensions) > 1
            else "design",
            "timeline": "3-6 months for significant improvement",
            "milestones": self._generate_milestones(sorted_dimensions),
        }

        return learning_path

    def _generate_milestones(self, sorted_dimensions: List[tuple]) -> List[str]:
        """Generate learning milestones based on performance"""
        if not sorted_dimensions:
            return []

        primary_weakness = sorted_dimensions[0][0]
        milestones = [
            f"Month 1: Focus on {primary_weakness} fundamentals",
            f"Month 2: Practice {primary_weakness} with real-world scenarios",
            f"Month 3: Integrate {primary_weakness} improvements with other skills",
        ]

        if len(sorted_dimensions) > 1:
            secondary_weakness = sorted_dimensions[1][0]
            milestones.extend(
                [
                    f"Month 4-5: Address {secondary_weakness} development",
                    "Month 6: Comprehensive practice integrating all skills",
                ]
            )

        return milestones

    def _analyze_performance_trends(
        self, responses: List[ResponseRecord]
    ) -> Dict[str, Any]:
        """Analyze performance trends across the interview"""
        if len(responses) < 2:
            return {"trend": "insufficient_data"}

        overall_scores = [r.scores.get("overall", 0) for r in responses if r.scores]
        if len(overall_scores) < 2:
            return {"trend": "insufficient_data"}

        first_half = overall_scores[: len(overall_scores) // 2]
        second_half = overall_scores[len(overall_scores) // 2 :]

        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)

        if second_avg > first_avg + 0.3:
            trend = "improving"
            trend_description = "Performance improved throughout the interview, showing good adaptability"
        elif first_avg > second_avg + 0.3:
            trend = "declining"
            trend_description = "Performance declined as interview progressed, possibly due to fatigue or increasing difficulty"
        else:
            trend = "consistent"
            trend_description = (
                "Maintained consistent performance throughout the interview"
            )

        return {
            "trend": trend,
            "description": trend_description,
            "first_half_avg": first_half,
            "second_half_avg": second_half,
        }

    def _generate_next_steps(
        self, responses: List[ResponseRecord], overall_score: float
    ) -> List[str]:
        """Generate specific next steps based on overall performance"""
        if overall_score >= 4.0:
            return [
                "Continue practicing advanced Excel scenarios to maintain expertise",
                "Consider mentoring others or teaching Excel skills",
                "Explore Excel automation with VBA or Power Query",
                "Stay updated with new Excel features and capabilities",
            ]
        elif overall_score >= 3.0:
            return [
                "Focus on areas identified for improvement while maintaining strengths",
                "Practice with more complex, real-world Excel scenarios",
                "Join Excel user communities for continued learning",
                "Consider advanced Excel training or certification",
            ]
        else:
            return [
                "Start with Excel fundamentals and basic functions",
                "Practice daily with simple Excel exercises",
                "Take a structured Excel course for beginners",
                "Focus on one skill area at a time for steady progress",
            ]

    def format_constructive_text_report(self, report: Dict[str, Any]) -> str:
        """Generate an enhanced constructive feedback report"""
        lines = [
            "# 📊 Excel Skills Interview - Constructive Feedback Report",
            "",
            f"**Session ID:** {report.get('session_id', 'N/A')}",
            f"**Date:** {str(report.get('timestamp', ''))[:19]}",
            f"**Duration:** {report.get('duration_minutes', 0):.1f} minutes",
            f"**Questions Answered:** {report.get('questions_answered', 0)}",
        ]

        # Add generation method indicator if available
        if report.get("generation_method") == "fallback_rule_based":
            lines.append(
                "*Note: Generated using fallback method due to AI service unavailability*"
            )

        lines.extend(
            [
                "",
                f"## 🎯 Overall Performance: {report.get('overall_score_normalized', 0):.0f}/100",
                f"*Raw Score: {report.get('overall_score', 0):.2f}/5.0*",
                "",
            ]
        )

        enhanced_feedback = report.get("enhanced_feedback", {})
        if enhanced_feedback:
            lines.extend(["## 📈 Detailed Skill Analysis", ""])

            for dimension, feedback in enhanced_feedback.items():
                # Handle both agent-generated and rule-based feedback structures
                current_level = feedback.get("current_level", "N/A")
                specific_feedback = feedback.get(
                    "specific_feedback", "No feedback available"
                )

                lines.extend(
                    [
                        f"### {dimension.title()}",
                        f"**Current Level:** {current_level}",
                        f"**Analysis:** {specific_feedback}",
                        "",
                    ]
                )

                # Handle improvement strategies
                strategies = feedback.get("improvement_strategies", [])
                if strategies:
                    lines.append("**Improvement Strategies:**")
                    for strategy in strategies:
                        lines.append(f"• {strategy}")
                    lines.append("")

                # Handle learning resources
                resources = feedback.get("resources", [])
                if resources:
                    lines.extend(["**Learning Resources:**"])
                    for resource in resources:
                        lines.append(f"• {resource}")
                    lines.append("")

        learning_path = report.get("learning_path", {})
        if learning_path:
            lines.extend(
                [
                    "## 🛤️ Personalized Learning Path",
                    "",
                    f"**Priority Focus:** {learning_path.get('priority_focus', 'N/A').title()}",
                ]
            )

            # Handle optional secondary focus
            secondary_focus = learning_path.get("secondary_focus")
            if secondary_focus:
                lines.append(f"**Secondary Focus:** {secondary_focus.title()}")

            timeline = learning_path.get("timeline", "N/A")
            lines.extend(
                [
                    f"**Recommended Timeline:** {timeline}",
                    "",
                ]
            )

            # Handle learning milestones
            milestones = learning_path.get("milestones", [])
            if milestones:
                lines.append("**Learning Milestones:**")
                for milestone in milestones:
                    lines.append(f"• {milestone}")
                lines.append("")

        next_steps = report.get("next_steps", [])
        if next_steps:
            lines.extend(["## 🚀 Immediate Next Steps", ""])

            for i, step in enumerate(next_steps, 1):
                lines.append(f"{i}. {step}")

            lines.append("")

        performance_trends = report.get("performance_trends", {})
        if (
            performance_trends
            and performance_trends.get("trend") != "insufficient_data"
        ):
            lines.extend(
                [
                    "## 📊 Performance Trends",
                    "",
                    f"**Trend:** {performance_trends.get('description', 'No trend analysis available')}",
                    "",
                ]
            )

        # Add question-by-question feedback if available
        detailed_responses = report.get("detailed_responses", [])
        if detailed_responses:
            lines.extend(["## 📝 Question-by-Question Feedback", ""])

            for response in detailed_responses:
                q_num = response.get("question_number", "?")
                overall_score = response.get("scores", {}).get("overall", 0)
                lines.extend(
                    [
                        f"### Question {q_num} (Score: {overall_score:.1f}/5.0)",
                        f"**Question:** {response.get('question', 'N/A')[:150]}{'...' if len(response.get('question', '')) > 150 else ''}",
                        f"**Your Response:** {response.get('answer_preview', 'No answer')}",
                        "",
                    ]
                )

                rationale = response.get("rationale", "")
                if rationale and rationale != "No evaluation rationale provided":
                    lines.extend([f"**Detailed Feedback:** {rationale}", ""])

        # Add raw statistics section
        lines.extend(
            [
                "---",
                "",
                "## 📊 Raw Statistics",
                "",
                "### Session Details",
                f"• **Session ID:** {report.get('session_id', 'N/A')}",
                f"• **Timestamp:** {report.get('timestamp', 'N/A')}",
                f"• **Duration:** {report.get('duration_minutes', 0):.1f} minutes",
                f"• **Questions Answered:** {report.get('questions_answered', 0)}",
                f"• **Overall Score (Raw):** {report.get('overall_score', 0):.3f}/5.0",
                f"• **Overall Score (Normalized):** {report.get('overall_score_normalized', 0):.1f}/100",
                "",
            ]
        )

        # Add detailed scores breakdown
        scores = report.get("scores", {})
        if scores:
            lines.extend(["### Score Breakdown by Dimension", ""])
            for dimension in [
                "correctness",
                "design",
                "communication",
                "production",
                "overall",
            ]:
                if dimension in scores:
                    score_data = scores[dimension]
                    lines.extend(
                        [
                            f"**{dimension.title()}:**",
                            f"  • Mean: {score_data.get('mean', 0):.3f}",
                            f"  • Median: {score_data.get('median', 0):.3f}",
                            f"  • Min: {score_data.get('min', 0):.3f}",
                            f"  • Max: {score_data.get('max', 0):.3f}",
                            f"  • Count: {score_data.get('count', 0)}",
                            "",
                        ]
                    )

        # Add strengths and weaknesses from base report
        strengths = report.get("strengths", [])
        if strengths:
            lines.extend(["### Identified Strengths", ""])
            for strength in strengths:
                lines.append(f"• {strength}")
            lines.append("")

        areas_for_improvement = report.get("areas_for_improvement", [])
        if areas_for_improvement:
            lines.extend(["### Areas for Improvement", ""])
            for area in areas_for_improvement:
                lines.append(f"• {area}")
            lines.append("")

        # Add metadata if available
        meta = report.get("meta", {})
        if meta:
            lines.extend(["### Technical Metadata", ""])
            for key, value in meta.items():
                lines.append(f"• **{key}:** {value}")
            lines.append("")

        lines.extend(
            [
                "---",
                "",
                "## 💡 Remember",
                "• Excel mastery comes with consistent practice",
                "• Focus on real-world applications to reinforce learning",
                "• Don't hesitate to explore Excel's extensive help documentation",
                "• Consider joining Excel communities for ongoing support",
                "",
                "*This report is designed to help you grow. Focus on progress, not perfection!*",
            ]
        )

        return "\n".join(lines)

    def generate_pdf_report(self, report: Dict[str, Any]) -> str:
        """Generate a PDF report and return the file path"""
        temp_dir = tempfile.gettempdir()
        session_id = report.get("session_id", "unknown")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"excel_interview_report_{session_id}_{timestamp}.pdf"
        filepath = os.path.join(temp_dir, filename)

        doc = SimpleDocTemplate(filepath, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            spaceAfter=30,
            textColor=HexColor("#2E86AB"),
            alignment=1,
        )

        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=HexColor("#A23B72"),
        )

        subheading_style = ParagraphStyle(
            "CustomSubHeading",
            parent=styles["Heading3"],
            fontSize=14,
            spaceAfter=8,
            spaceBefore=12,
            textColor=HexColor("#F18F01"),
        )

        story.append(Paragraph("Excel Skills Interview Report", title_style))
        story.append(Spacer(1, 20))

        story.append(Paragraph("Session Information", heading_style))
        session_data = [
            ["Session ID:", report.get("session_id", "N/A")],
            ["Date:", str(report.get("timestamp", ""))[:19]],
            ["Duration:", f"{report.get('duration_minutes', 0):.1f} minutes"],
            ["Questions Answered:", str(report.get("questions_answered", 0))],
        ]

        session_table = Table(session_data, colWidths=[2 * inch, 3 * inch])
        session_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), HexColor("#F0F0F0")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ]
            )
        )

        story.append(session_table)
        story.append(Spacer(1, 20))

        overall_score = report.get("overall_score_normalized", 0)
        story.append(
            Paragraph(f"Overall Score: {overall_score:.0f}/100", heading_style)
        )
        story.append(
            Paragraph(
                f"Raw Score: {report.get('overall_score', 0):.2f}/5.0", styles["Normal"]
            )
        )
        story.append(Spacer(1, 15))

        enhanced_feedback = report.get("enhanced_feedback", {})
        if enhanced_feedback:
            story.append(Paragraph("Detailed Skill Analysis", heading_style))

            for dimension, feedback in enhanced_feedback.items():
                story.append(Paragraph(dimension.title(), subheading_style))
                story.append(
                    Paragraph(
                        f"<b>Current Level:</b> {feedback.get('current_level', 'N/A')}",
                        styles["Normal"],
                    )
                )
                story.append(
                    Paragraph(
                        f"<b>Analysis:</b> {feedback.get('specific_feedback', 'No feedback available')}",
                        styles["Normal"],
                    )
                )

                strategies = feedback.get("improvement_strategies", [])
                if strategies:
                    story.append(
                        Paragraph("<b>Improvement Strategies:</b>", styles["Normal"])
                    )
                    for strategy in strategies[:3]:
                        story.append(Paragraph(f"• {strategy}", styles["Normal"]))

                story.append(Spacer(1, 10))

        learning_path = report.get("learning_path", {})
        if learning_path:
            story.append(Paragraph("Personalized Learning Path", heading_style))
            story.append(
                Paragraph(
                    f"<b>Priority Focus:</b> {learning_path.get('priority_focus', 'N/A').title()}",
                    styles["Normal"],
                )
            )
            story.append(
                Paragraph(
                    f"<b>Timeline:</b> {learning_path.get('timeline', 'N/A')}",
                    styles["Normal"],
                )
            )

            milestones = learning_path.get("milestones", [])
            if milestones:
                story.append(Paragraph("<b>Learning Milestones:</b>", styles["Normal"]))
                for milestone in milestones[:3]:
                    story.append(Paragraph(f"• {milestone}", styles["Normal"]))

            story.append(Spacer(1, 15))

        next_steps = report.get("next_steps", [])
        if next_steps:
            story.append(Paragraph("Immediate Next Steps", heading_style))
            for i, step in enumerate(next_steps[:4], 1):
                story.append(Paragraph(f"{i}. {step}", styles["Normal"]))
            story.append(Spacer(1, 15))

        detailed_responses = report.get("detailed_responses", [])
        if detailed_responses:
            story.append(Paragraph("Question Summary", heading_style))

            for response in detailed_responses[:3]:
                q_num = response.get("question_number", "?")
                overall_score = response.get("scores", {}).get("overall", 0)
                story.append(
                    Paragraph(
                        f"Question {q_num} (Score: {overall_score:.1f}/5.0)",
                        subheading_style,
                    )
                )

                question_text = response.get("question", "N/A")
                if len(question_text) > 200:
                    question_text = question_text[:200] + "..."
                story.append(
                    Paragraph(f"<b>Question:</b> {question_text}", styles["Normal"])
                )

                answer_preview = response.get("answer_preview", "No answer")
                story.append(
                    Paragraph(
                        f"<b>Your Response:</b> {answer_preview}", styles["Normal"]
                    )
                )

                rationale = response.get("rationale", "")
                if rationale and rationale != "No evaluation rationale provided":
                    if len(rationale) > 300:
                        rationale = rationale[:300] + "..."
                    story.append(
                        Paragraph(f"<b>Feedback:</b> {rationale}", styles["Normal"])
                    )

                story.append(Spacer(1, 10))

        # Add raw statistics section
        story.append(Spacer(1, 20))
        story.append(Paragraph("Raw Statistics", heading_style))

        # Session details
        story.append(Paragraph("<b>Session Details:</b>", styles["Normal"]))
        story.append(
            Paragraph(
                f"• Session ID: {report.get('session_id', 'N/A')}", styles["Normal"]
            )
        )
        story.append(
            Paragraph(
                f"• Timestamp: {report.get('timestamp', 'N/A')}", styles["Normal"]
            )
        )
        story.append(
            Paragraph(
                f"• Duration: {report.get('duration_minutes', 0):.1f} minutes",
                styles["Normal"],
            )
        )
        story.append(
            Paragraph(
                f"• Questions Answered: {report.get('questions_answered', 0)}",
                styles["Normal"],
            )
        )
        story.append(
            Paragraph(
                f"• Overall Score (Raw): {report.get('overall_score', 0):.3f}/5.0",
                styles["Normal"],
            )
        )
        story.append(
            Paragraph(
                f"• Overall Score (Normalized): {report.get('overall_score_normalized', 0):.1f}/100",
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 10))

        # Detailed scores breakdown
        scores = report.get("scores", {})
        if scores:
            story.append(
                Paragraph("<b>Score Breakdown by Dimension:</b>", styles["Normal"])
            )
            for dimension in [
                "correctness",
                "design",
                "communication",
                "production",
                "overall",
            ]:
                if dimension in scores:
                    score_data = scores[dimension]
                    story.append(
                        Paragraph(f"<b>{dimension.title()}:</b>", styles["Normal"])
                    )
                    story.append(
                        Paragraph(
                            f"  Mean: {score_data.get('mean', 0):.3f}, Median: {score_data.get('median', 0):.3f}",
                            styles["Normal"],
                        )
                    )
                    story.append(
                        Paragraph(
                            f"  Min: {score_data.get('min', 0):.3f}, Max: {score_data.get('max', 0):.3f}, Count: {score_data.get('count', 0)}",
                            styles["Normal"],
                        )
                    )
            story.append(Spacer(1, 10))

        # Add strengths and weaknesses
        strengths = report.get("strengths", [])
        if strengths:
            story.append(Paragraph("<b>Identified Strengths:</b>", styles["Normal"]))
            for strength in strengths:
                story.append(Paragraph(f"• {strength}", styles["Normal"]))
            story.append(Spacer(1, 5))

        areas_for_improvement = report.get("areas_for_improvement", [])
        if areas_for_improvement:
            story.append(Paragraph("<b>Areas for Improvement:</b>", styles["Normal"]))
            for area in areas_for_improvement:
                story.append(Paragraph(f"• {area}", styles["Normal"]))
            story.append(Spacer(1, 5))

        # Add metadata if available
        meta = report.get("meta", {})
        if meta:
            story.append(Paragraph("<b>Technical Metadata:</b>", styles["Normal"]))
            for key, value in meta.items():
                story.append(Paragraph(f"• {key}: {value}", styles["Normal"]))

        story.append(Spacer(1, 20))
        story.append(
            Paragraph(
                "Remember: Excel mastery comes with consistent practice. Focus on progress, not perfection!",
                styles["Italic"],
            )
        )

        doc.build(story)
        return filepath
