import logging
from datetime import datetime, timezone

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from src.interview_engine.models import Question, InterviewState

logger = logging.getLogger(__name__)


class QuestionGenerator:
    def __init__(self, model_name: str = "gemini-2.5-flash", temperature: float = 0.3):
        self.model_name = model_name
        self.temperature = temperature
        self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=temperature)

        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", self._get_system_prompt()),
                ("human", self._get_generation_prompt()),
            ]
        )

        self.parser = JsonOutputParser()
        self.chain = self.prompt_template | self.llm | self.parser

    def _get_system_prompt(self) -> str:
        return """You are an intelligent technical interviewer that generates follow-up questions based on the candidate's responses and interview progress.

        Your role is to:
        1. Analyze the candidate's previous responses to understand their technical level and areas of strength/weakness
        2. Generate appropriate follow-up questions that progressively assess their skills
        3. Adapt question difficulty based on their performance
        4. Explore different technical areas while building on previous conversations

        Return a JSON object with this exact schema:
        {{
        "question": "The next interview question text",
        "type": "qa",
        "difficulty": "beginner|intermediate|advanced", 
        "category": "database|data_engineering|distributed_systems|programming|system_design|other",
        "reasoning": "Brief explanation of why this question follows logically from the conversation"
        }}

        Guidelines:
        - Questions should be technical and relevant to data/software engineering roles
        - Build on previous responses - if they showed SQL knowledge, dive deeper or explore related areas
        - If they struggled with a concept, ask a simpler related question or move to a different area
        - Keep questions focused and clear
        - Avoid repeating similar questions
        - Progress from basic to advanced topics naturally
        """

    def _get_generation_prompt(self) -> str:
        return """INTERVIEW CONTEXT:
        Current Phase: {phase}
        Questions Asked: {questions_count}
        Target Total Questions: {target_questions}

        CHAT HISTORY:
        {chat_history}

        CANDIDATE PERFORMANCE SUMMARY:
        {performance_summary}

        Generate the next appropriate interview question that:
        1. Builds naturally on the conversation so far
        2. Assesses the candidate's technical abilities appropriately
        3. Explores new areas or goes deeper into areas they've shown competence
        4. Matches their demonstrated skill level

        Return the question in the specified JSON format.
        """

    def generate_next_question(self, state: InterviewState) -> Question:
        try:
            chat_history = self._format_chat_history(state)
            performance_summary = self._analyze_performance(state)

            result = self.chain.invoke(
                {
                    "phase": state.phase,
                    "questions_count": len(state.responses),
                    "target_questions": 4,
                    "chat_history": chat_history,
                    "performance_summary": performance_summary,
                }
            )

            question_id = f"q{len(state.responses) + 1}"

            return Question(
                id=question_id,
                text=result.get(
                    "question", "Tell me about your experience with data processing."
                ),
                type=result.get("type", "qa"),
                metadata={
                    "category": result.get("category", "general"),
                    "difficulty": result.get("difficulty", "intermediate"),
                    "reasoning": result.get("reasoning", "Generated dynamically"),
                    "generated_at": datetime.now(tz=timezone.utc).isoformat(),
                },
            )

        except Exception as e:
            logger.error(f"Failed to generate question: {e}")
            return self._create_fallback_question(state)

    def _format_chat_history(self, state: InterviewState) -> str:
        if not state.responses:
            return "No previous responses yet - this is the first question."

        history_parts = []
        for i, response in enumerate(state.responses, 1):
            history_parts.append(f"Q{i}: {response.question_text}")
            history_parts.append(f"A{i}: {response.answer_text}")
            if response.scores and response.rationale:
                overall_score = response.scores.get("overall", 0)
                history_parts.append(
                    f"Score: {overall_score:.1f}/5.0 - {response.rationale}"
                )
            history_parts.append("")

        return "\n".join(history_parts)

    def _analyze_performance(self, state: InterviewState) -> str:
        if not state.responses:
            return "No performance data yet - first question."

        total_responses = len(state.responses)

        avg_scores = {}
        score_dimensions = [
            "correctness",
            "design",
            "communication",
            "production",
            "overall",
        ]

        for dim in score_dimensions:
            scores = [r.scores.get(dim, 0) for r in state.responses if r.scores]
            avg_scores[dim] = sum(scores) / len(scores) if scores else 0

        strengths = []
        weaknesses = []

        for dim, avg_score in avg_scores.items():
            if avg_score >= 4.0:
                strengths.append(dim)
            elif avg_score <= 2.5:
                weaknesses.append(dim)

        categories_covered = set()
        for response in state.responses:
            if hasattr(response, "question_text"):
                for question in state.questions:
                    if question.text == response.question_text and question.metadata:
                        categories_covered.add(
                            question.metadata.get("category", "general")
                        )

        summary_parts = [
            f"Total responses: {total_responses}",
            f"Average overall score: {avg_scores['overall']:.1f}/5.0",
        ]

        if strengths:
            summary_parts.append(f"Strong areas: {', '.join(strengths)}")
        if weaknesses:
            summary_parts.append(f"Areas for improvement: {', '.join(weaknesses)}")
        if categories_covered:
            summary_parts.append(
                f"Categories explored: {', '.join(categories_covered)}"
            )

        return " | ".join(summary_parts)

    def _create_fallback_question(self, state: InterviewState) -> Question:
        fallback_questions = [
            "How do you approach debugging a complex technical issue?",
            "Describe a challenging technical project you've worked on recently.",
            "What's your experience with database optimization?",
            "How do you ensure code quality in your development process?",
            "Tell me about your experience with distributed systems.",
        ]

        question_index = len(state.responses) % len(fallback_questions)
        question_text = fallback_questions[question_index]

        return Question(
            id=f"fallback_q{len(state.responses) + 1}",
            text=question_text,
            type="qa",
            metadata={
                "category": "general",
                "difficulty": "intermediate",
                "reasoning": "Fallback question due to generation error",
                "generated_at": datetime.now(tz=timezone.utc).isoformat(),
            },
        )

    def generate_scenario_question(self, state: InterviewState) -> str:
        try:
            scenario_prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are generating a technical scenario question for an interview. 
                Based on the candidate's performance so far, create a relevant scenario that tests their problem-solving abilities.
                Return only the scenario question text, no additional formatting.""",
                    ),
                    (
                        "human",
                        """Based on this interview context:
                {chat_history}
                
                Performance: {performance_summary}
                
                Generate a practical scenario question that:
                1. Tests problem-solving and system thinking
                2. Is appropriate for their demonstrated skill level
                3. Relates to their areas of strength or explores new territory
                4. Is realistic and engaging
                
                Return just the scenario question text.""",
                    ),
                ]
            )

            scenario_chain = scenario_prompt | self.llm

            chat_history = self._format_chat_history(state)
            performance_summary = self._analyze_performance(state)

            result = scenario_chain.invoke(
                {
                    "chat_history": chat_history,
                    "performance_summary": performance_summary,
                }
            )

            return result.content

        except Exception as e:
            logger.error(f"Failed to generate scenario question: {e}")
            return """**Scenario:** You're working on a web application that has become very slow. Users are complaining about page load times exceeding 10 seconds. 

Walk me through your approach to diagnose and fix this performance issue. What tools would you use, what would you investigate first, and what are some common causes and solutions you'd consider?"""

    def generate_reflection_question(self, state: InterviewState) -> str:
        try:
            reflection_prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """Generate a thoughtful reflection question for the end of a technical interview.
                The question should help the candidate reflect on their learning and growth areas.
                Return only the question text.""",
                    ),
                    (
                        "human",
                        """Based on this interview:
                {chat_history}
                
                Generate a reflection question that helps the candidate think about:
                1. Their learning and development goals
                2. Areas they want to improve based on the interview
                3. Their technical interests and career direction
                
                Return just the reflection question text.""",
                    ),
                ]
            )

            reflection_chain = reflection_prompt | self.llm

            chat_history = self._format_chat_history(state)

            result = reflection_chain.invoke({"chat_history": chat_history})

            return result.content

        except Exception as e:
            logger.error(f"Failed to generate reflection question: {e}")
            return """**Reflection:** Looking back at this interview, what's one technical area you'd like to improve or learn more about? What would be your plan to develop that skill?"""
