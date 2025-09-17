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
        return """You are an experienced Excel interviewer conducting a conversational interview. You must respond ONLY with valid JSON - no additional text before or after.

        CRITICAL: Your response must be valid JSON in this EXACT format:
        {{
        "text": "Your complete conversational response (acknowledgment + next question/comment)",
        "phase_transition": false,
        "new_phase": null,
        "coverage_assessment": "Brief note on what domains you've covered and what's still needed",
        "reasoning": "Why you're asking this question or making this transition"
        }}

        INTERVIEW BEHAVIOR:
        - Be conversational and warm, but professional
        - Reference previous answers when relevant
        - Adapt difficulty based on their responses
        - Show genuine curiosity about their Excel expertise

        ADAPTIVE STRATEGIES:
        - Strong answers → ask deeper/more complex questions
        - Weak answers → simplify or try different angle
        - Partial knowledge → probe to understand their actual level

        IMPORTANT: Return ONLY the JSON object, nothing else. No markdown, no explanations, just pure JSON.
        
        Example valid response:
        {{"text": "Great! Now I'm curious about your experience with PivotTables. Can you walk me through how you'd create one?", "phase_transition": false, "new_phase": null, "coverage_assessment": "Covered formulas, now exploring PivotTables", "reasoning": "Moving to next core Excel domain"}}"""

    def _get_generation_prompt(self) -> str:
        return """INTERVIEW CONTEXT:
        Current Phase: {phase}
        Questions Asked: {questions_count}
        Target Total Questions: {target_questions}

        CONVERSATION HISTORY:
        {chat_history}

        CANDIDATE PERFORMANCE ANALYSIS:
        {performance_summary}

        INTERVIEW TIMING:
        {time_status}

        INSTRUCTIONS FOR YOUR NEXT RESPONSE:
        You are an experienced Excel interviewer with full control over the interview flow. Your goal is to assess the candidate across these core Excel domains:

        **REQUIRED COVERAGE AREAS:**
        1. Data entry/cleanup (data validation, formatting, cleaning techniques)
        2. Formulas & functions (VLOOKUP, INDEX/MATCH, complex formulas)
        3. PivotTables & summarization (creating, customizing, analyzing data)
        4. Scenario/what-if analysis (Goal Seek, data tables, scenario manager)
        5. Reflection/meta question (learning approach, problem-solving process)

        **YOU CONTROL THE INTERVIEW FLOW:**
        - **Topic Switching**: Decide when you're satisfied with their knowledge in an area and want to move to another domain
        - **Follow-up Depth**: Decide how many follow-ups are needed before you have "enough evidence"
        - **Phase Transitions**: Decide when to move from Q&A to reflection to closing based on coverage and time
        - **Pacing**: Adapt your questioning speed based on their responses and remaining time

        **DECISION MAKING:**
        - If you need more evidence in current area → continue with follow-ups (phase_transition: false)
        - If satisfied with current area → switch to uncovered domain (phase_transition: false, new question)  
        - If you've covered enough domains → move to reflection (phase_transition: true, new_phase: "reflection")
        - If reflection is done → close interview (phase_transition: true, new_phase: "closing")

        **TIME AWARENESS:**
        - Use remaining time efficiently to ensure core coverage
        - At 12+ minutes, prioritize uncovered areas
        - Don't rush, but be strategic about depth vs breadth

        Return the question in the specified JSON format.
        """

    def generate_next_response(
        self, state: InterviewState, time_status: dict = None
    ) -> dict:
        try:
            chat_history = self._format_chat_history(state)
            performance_summary = self._analyze_performance(state)

            if time_status is None:
                current_time = datetime.now(tz=timezone.utc)
                elapsed = current_time - state.start_time
                elapsed_minutes = elapsed.total_seconds() / 60.0
                time_status = {
                    "elapsed_minutes": elapsed_minutes,
                    "remaining_minutes": max(0, 15 - elapsed_minutes),
                    "time_up": elapsed_minutes >= 15,
                    "time_warning": elapsed_minutes >= 12,
                }

            # Prepare variables for template with safe defaults
            try:
                formatted_time_status = self._format_time_status(time_status)
            except Exception as e:
                logger.error(f"Error formatting time status: {e}")
                formatted_time_status = "Time status unavailable"

            template_vars = {
                "phase": str(state.phase or "qa"),
                "questions_count": len(state.responses or []),
                "target_questions": "No fixed target - you decide when enough coverage is achieved",
                "chat_history": str(
                    chat_history
                    or "No previous responses yet - this is the first question."
                ),
                "performance_summary": str(
                    performance_summary or "Starting interview assessment"
                ),
                "time_status": formatted_time_status,
            }

            # Debug log the variables
            logger.debug(f"Template variables: {template_vars}")

            try:
                result = self.chain.invoke(template_vars)
            except Exception as parse_error:
                logger.error(f"JSON parsing failed: {parse_error}")
                # Try to get the raw response and fix it
                try:
                    raw_chain = self.prompt_template | self.llm
                    raw_result = raw_chain.invoke(template_vars)
                    logger.error(
                        f"Raw LLM response that failed to parse: {raw_result.content}"
                    )
                    # Try to validate and fix the response
                    result = self._validate_and_fix_json_response(raw_result.content)
                except Exception as e:
                    logger.error(f"Could not get or fix raw response: {e}")
                    # Final fallback response
                    result = {
                        "text": "Let me start by asking about your Excel experience. How comfortable are you with creating formulas and functions?",
                        "phase_transition": False,
                        "new_phase": None,
                        "coverage_assessment": "Starting with formulas assessment",
                        "reasoning": "Fallback due to JSON parsing error",
                    }

            if not result.get("phase_transition", False):
                question_id = f"q{len(state.responses) + 1}"
                question = Question(
                    id=question_id,
                    text=result.get("text", "Tell me about your Excel experience."),
                    type="qa",
                    metadata={
                        "coverage_assessment": result.get("coverage_assessment", ""),
                        "reasoning": result.get("reasoning", "Generated dynamically"),
                        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
                    },
                )
                state.questions.append(question)

            return {
                "text": result.get("text", "Let me ask about your Excel experience."),
                "phase_transition": result.get("phase_transition", False),
                "new_phase": result.get("new_phase"),
                "coverage_assessment": result.get("coverage_assessment", ""),
                "reasoning": result.get("reasoning", ""),
            }

        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return {
                "text": "Let me ask you about your Excel experience. How comfortable are you with creating and working with formulas?",
                "phase_transition": False,
                "new_phase": None,
                "coverage_assessment": "Starting with formulas assessment",
                "reasoning": "Fallback question due to generation error",
            }

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
            return "First question - no performance data yet. Start with a foundational technical question to gauge their level."

        total_responses = len(state.responses)
        latest_response = state.responses[-1] if state.responses else None

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
        moderate_areas = []

        for dim, avg_score in avg_scores.items():
            if avg_score >= 4.0:
                strengths.append(dim)
            elif avg_score <= 2.5:
                weaknesses.append(dim)
            else:
                moderate_areas.append(dim)

        categories_covered = set()
        difficulty_trend = []

        for i, response in enumerate(state.responses):
            if hasattr(response, "question_text"):
                for question in state.questions:
                    if question.text == response.question_text and question.metadata:
                        categories_covered.add(
                            question.metadata.get("category", "general")
                        )
                        difficulty_trend.append(
                            question.metadata.get("difficulty", "intermediate")
                        )

        last_question_difficulty = (
            difficulty_trend[-1] if difficulty_trend else "intermediate"
        )
        last_score = (
            latest_response.scores.get("overall", 0)
            if latest_response and latest_response.scores
            else 0
        )

        performance_trend = "stable"
        if len(state.responses) >= 2:
            recent_scores = [
                r.scores.get("overall", 0) for r in state.responses[-2:] if r.scores
            ]
            if len(recent_scores) == 2:
                if recent_scores[1] > recent_scores[0] + 0.5:
                    performance_trend = "improving"
                elif recent_scores[1] < recent_scores[0] - 0.5:
                    performance_trend = "declining"

        adaptive_guidance = ""
        if last_score >= 4.0:
            adaptive_guidance = "INCREASE DIFFICULTY - Last answer was strong, push harder with optimization/edge cases"
        elif last_score <= 1.5:
            adaptive_guidance = "INADEQUATE RESPONSE - Last answer was insufficient (likely 'no', 'yes', or minimal). STAY ON SAME TOPIC and ask follow-up questions to get them to elaborate. Don't move to new topics."
        elif last_score <= 2.5:
            adaptive_guidance = "DECREASE DIFFICULTY - Last answer struggled, simplify or pivot to their strengths"
        else:
            adaptive_guidance = "PROBE DEEPER - Last answer was partial, explore their understanding further"

        summary_parts = [
            f"Responses: {total_responses}",
            f"Overall avg: {avg_scores['overall']:.1f}/5.0",
            f"Last score: {last_score:.1f}/5.0 ({last_question_difficulty})",
            f"Trend: {performance_trend}",
            adaptive_guidance,
        ]

        if strengths:
            summary_parts.append(f"Strengths: {', '.join(strengths)}")
        if weaknesses:
            summary_parts.append(f"Weaknesses: {', '.join(weaknesses)}")
        if categories_covered:
            summary_parts.append(f"Topics covered: {', '.join(categories_covered)}")

        if latest_response and latest_response.rationale:
            summary_parts.append(f"Last feedback: {latest_response.rationale[:100]}...")

        return " | ".join(summary_parts)

    def _format_time_status(self, time_status: dict) -> str:
        """Format timing information for the prompt"""
        if not time_status:
            return "Time status unavailable"

        elapsed = time_status.get("elapsed_minutes", 0)
        remaining = time_status.get("remaining_minutes", 15)

        status_parts = [
            f"Elapsed: {elapsed:.1f} minutes",
            f"Remaining: {remaining:.1f} minutes",
        ]

        if time_status.get("time_up", False):
            status_parts.append("TIME UP - Should move to reflection")
        elif time_status.get("time_warning", False):
            status_parts.append("TIME WARNING - Interview should wrap up soon")
        else:
            status_parts.append("Time available for more questions")

        return " | ".join(status_parts)

    def _validate_and_fix_json_response(self, raw_response: str) -> dict:
        """Validate and attempt to fix JSON responses from the LLM"""
        try:
            import json

            # Try to parse as-is first
            return json.loads(raw_response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown or other formatting
            import re

            # Look for JSON in code blocks
            json_match = re.search(
                r"```json\s*(\{.*?\})\s*```", raw_response, re.DOTALL
            )
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

            # Look for JSON without code blocks
            json_match = re.search(r"(\{.*?\})", raw_response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

            # If all else fails, return a fallback response
            logger.warning(f"Could not parse JSON response: {raw_response}")
            return {
                "text": "Let me ask about your Excel experience. What's your comfort level with formulas and functions?",
                "phase_transition": False,
                "new_phase": None,
                "coverage_assessment": "Starting Excel assessment",
                "reasoning": "Fallback due to unparseable response",
            }

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
                        """You are a conversational technical interviewer creating a practical scenario question. 
                Your personality is warm, curious, and genuinely interested in the candidate's problem-solving approach.
                
                Create a scenario that:
                - Starts with a natural acknowledgment of their previous responses
                - Feels like a natural continuation of your conversation
                - References or builds upon topics you've already discussed  
                - Tests their practical problem-solving and system thinking
                - Is presented in a conversational, engaging way
                
                Include natural transitions like "That's been really helpful! Now I'd like to shift to..." or "Great insights so far. Let's try a different kind of question..." or "I'm getting a good sense of your background. Now I'm curious how you'd approach..."
                Return the complete conversational response including acknowledgment and scenario question.""",
                    ),
                    (
                        "human",
                        """Based on our conversation so far:
                {chat_history}
                
                Candidate insights: {performance_summary}
                
                Now I want to shift to a practical scenario that:
                1. Builds on topics we've discussed or their demonstrated expertise
                2. Tests their real-world problem-solving approach
                3. Matches their technical level and interests
                4. Feels like a natural next step in our conversation
                
                Create a conversational scenario question that references our previous discussion and presents an engaging real-world challenge. Use a warm, curious tone like you're genuinely interested in their approach.""",
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
            return """Thanks for sharing your insights so far - I'm getting a good sense of your technical background! Now I'd love to shift gears and explore your problem-solving approach with a practical scenario.

Imagine you're working on a web application that has become very slow - users are complaining about page load times exceeding 10 seconds. This is the kind of challenge that can really test your systematic thinking.

I'm curious: how would you approach diagnosing and fixing this performance issue? Walk me through your thought process - what tools would you reach for first, what would you investigate, and what are some of the common culprits you'd consider?"""

    def generate_reflection_question(
        self, state: InterviewState, time_status: dict = None
    ) -> str:
        try:
            reflection_prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are a thoughtful technical interviewer wrapping up a conversational interview.
                Your personality is warm, encouraging, and genuinely interested in the candidate's growth journey.
                
                Create a reflection question that:
                - Starts with a natural acknowledgment of their scenario response and overall conversation
                - Feels like a natural, supportive conclusion to your conversation
                - References specific topics or insights from your discussion
                - Encourages the candidate to think about their learning journey
                - Shows genuine interest in their professional development
                
                Include natural transitions like "That was excellent problem-solving! As we wrap up..." or "I really appreciate how you worked through that. To close out our conversation..." or "Thanks for sharing your approach to that challenge. Before we finish..."
                
                TIME AWARENESS: If the interview reached the 15-minute time limit, acknowledge this naturally: "I notice we've reached our time limit, so let's wrap up with a quick reflection..." or "Time flies when you're having a good technical discussion! Let's close with..."
                
                Return the complete conversational response including acknowledgment and reflection question.""",
                    ),
                    (
                        "human",
                        """Based on our wonderful conversation:
                {chat_history}
                
                Interview timing: {time_status}
                
                As we wrap up, I'd love to end on a reflective note that helps them think about:
                1. Their learning and development journey
                2. Areas they're excited to grow in (perhaps inspired by our discussion)
                3. Their technical interests and where they want to head next
                
                Create a warm, encouraging reflection question that references our conversation and shows genuine interest in their growth. Make it feel like a supportive mentor asking about their development goals.""",
                    ),
                ]
            )

            reflection_chain = reflection_prompt | self.llm

            chat_history = self._format_chat_history(state)

            # Calculate time status if not provided
            if time_status is None:
                from datetime import datetime, timezone

                current_time = datetime.now(tz=timezone.utc)
                elapsed = current_time - state.start_time
                elapsed_minutes = elapsed.total_seconds() / 60.0
                time_status = {
                    "elapsed_minutes": elapsed_minutes,
                    "remaining_minutes": max(0, 15 - elapsed_minutes),
                    "time_up": elapsed_minutes >= 15,
                    "time_warning": elapsed_minutes >= 12,
                }

            result = reflection_chain.invoke(
                {
                    "chat_history": chat_history,
                    "time_status": self._format_time_status(time_status),
                }
            )

            return result.content

        except Exception as e:
            logger.error(f"Failed to generate reflection question: {e}")
            return """That was really insightful - I appreciate how you worked through that challenge! As we wrap up our conversation, I'm really curious about your learning journey. 

Looking back at our discussion today - and thinking about your technical interests and goals - what's one area you're excited to dive deeper into or improve? It could be something we touched on today, or perhaps something you've been thinking about lately.

I'd love to hear not just what you want to learn, but also how you're thinking about approaching that growth. What's your plan or strategy for developing in that area?"""

    def generate_reflection_response(
        self, state: InterviewState, time_status: dict = None
    ) -> dict:
        """Generate reflection response with agent control over when to close the interview"""
        try:
            from datetime import datetime, timezone

            reflection_prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are an experienced Excel interviewer in the reflection phase. You have control over when to end the interview.

                        Your response should be a JSON with this schema:
                        {{
                        "text": "Your conversational response",
                        "phase_transition": false,
                        "new_phase": null,
                        "assessment_complete": "Whether you have enough information to provide meaningful feedback"
                        }}

                        DECISION MAKING:
                        - If you need more reflection/insight → continue conversation (phase_transition: false)
                        - If you have sufficient information → end interview (phase_transition: true, new_phase: "closing")
                        
                        TIME AWARENESS: If time is very limited, wrap up efficiently but meaningfully.""",
                    ),
                    (
                        "human",
                        """Based on our conversation:
                        {chat_history}
                        
                        Interview timing: {time_status}
                        
                        Decide whether to continue the reflection or conclude the interview based on the depth of information gathered.""",
                    ),
                ]
            )

            reflection_chain = reflection_prompt | self.llm

            chat_history = self._format_chat_history(state)

            # Calculate time status if not provided
            if time_status is None:
                current_time = datetime.now(tz=timezone.utc)
                elapsed = current_time - state.start_time
                elapsed_minutes = elapsed.total_seconds() / 60.0
                time_status = {
                    "elapsed_minutes": elapsed_minutes,
                    "remaining_minutes": max(0, 15 - elapsed_minutes),
                    "time_up": elapsed_minutes >= 15,
                    "time_warning": elapsed_minutes >= 12,
                }

            result = reflection_chain.invoke(
                {
                    "chat_history": chat_history,
                    "time_status": self._format_time_status(time_status),
                }
            )

            return {
                "text": result.get("text", "Thank you for that reflection."),
                "phase_transition": result.get("phase_transition", False),
                "new_phase": result.get("new_phase"),
                "assessment_complete": result.get("assessment_complete", ""),
            }

        except Exception as e:
            logger.error(f"Failed to generate reflection response: {e}")
            return {
                "text": "Thank you for sharing your thoughts on learning and growth. That gives me great insight into your approach to professional development.",
                "phase_transition": True,
                "new_phase": "closing",
                "assessment_complete": "Sufficient information gathered",
            }
