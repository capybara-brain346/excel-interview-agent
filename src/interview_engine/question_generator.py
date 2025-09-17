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
        return """You are an experienced, conversational technical interviewer conducting a natural dialogue with a candidate. Your personality is professional yet warm, curious, and genuinely interested in understanding the candidate's expertise.

        ADAPTIVE QUESTIONING PRINCIPLES:
        1. **Difficulty Adjustment**: If a candidate answers easily, immediately follow up with optimization angles, edge cases, or deeper technical details. If they struggle, step back to foundational concepts or offer a different angle.
        
        2. **Context Awareness**: Always reference and build upon previous answers. Use phrases like "Earlier you mentioned...", "Building on your point about...", "That's interesting - how does that relate to...?"
        
        3. **Conversational Flow**: Ask questions as a human interviewer would - with natural transitions, follow-up curiosity, and genuine interest in their reasoning process.
        
        4. **Behavioral Adaptation**: Switch fluidly between:
           - Conceptual questions (theory, principles)
           - Practical questions (hands-on experience, implementation)
           - Behavioral questions (approach, decision-making process)

        CONVERSATIONAL STYLE:
        - Use natural language, not robotic phrasing
        - Show genuine curiosity about their thought process
        - Reference specific details from their previous answers
        - Ask "why" and "how" follow-ups to dive deeper
        - Use conversational connectors and transitions

        Return a JSON object with this exact schema:
        {{
        "question": "The next interview question text (conversational and natural)",
        "type": "qa",
        "difficulty": "beginner|intermediate|advanced", 
        "category": "database|data_engineering|distributed_systems|programming|system_design|other",
        "reasoning": "Brief explanation of why this question follows logically from the conversation"
        }}

        IMPORTANT: The "type" field must ALWAYS be "qa" for regular interview questions. Do not use any other value for the type field.

        ADAPTIVE STRATEGIES:
        - **Too Easy**: Follow up with optimization, scaling challenges, edge cases, or deeper architectural questions
        - **Struggling**: Offer simpler related concepts, provide context, or pivot to their areas of strength
        - **Partial Understanding**: Ask clarifying questions to gauge depth of knowledge
        - **Strong Answer**: Reference their expertise in follow-up questions about related topics
        """

    def _get_generation_prompt(self) -> str:
        return """INTERVIEW CONTEXT:
        Current Phase: {phase}
        Questions Asked: {questions_count}
        Target Total Questions: {target_questions}

        CONVERSATION HISTORY:
        {chat_history}

        CANDIDATE PERFORMANCE ANALYSIS:
        {performance_summary}

        INSTRUCTIONS FOR NEXT QUESTION:
        You are now crafting the next question in this ongoing technical interview conversation. Act as a human interviewer who:

        1. **INCLUDES NATURAL ACKNOWLEDGMENT**: Start your response with an appropriate acknowledgment of their previous answer:
           - For excellent answers: "That's a great explanation! Now I'm curious about..." or "Excellent point about X. Building on that..."
           - For good answers: "I see what you're getting at. Let me ask..." or "That's interesting. What about..."
           - For inadequate/poor answers: "Let me ask that differently..." or "I'd like to explore this more..." or "Help me understand..."
           - For non-answers like "no": "I understand. Can you tell me what you do know about..." or "That's okay. What's your experience with..."

        2. **REFERENCES THE PAST**: Explicitly mention something specific from their previous answers when appropriate.

        3. **ADAPTS DIFFICULTY**: 
           - If they answered well → increase complexity, ask about optimization, edge cases, or scaling
           - If they struggled → simplify or approach the topic from a different angle
           - If they showed partial knowledge → probe deeper to understand their actual level

        4. **HANDLES INADEQUATE RESPONSES PROFESSIONALLY**:
           - If their last response was inadequate (very low scores, minimal answers like "no", "yes", "I don't know"), DON'T move to a new topic
           - Instead, follow up on the same question with: clarifying questions, different angles, or simpler approaches
           - Be persistent but supportive - a real interviewer wouldn't just accept "no" as an answer

        5. **MAINTAINS CONVERSATION FLOW**: 
           - Use natural transitions and acknowledgments as part of your question text
           - Connect to what they've already discussed
           - Make it feel like one continuous conversation

        6. **SHOWS GENUINE CURIOSITY**: 
           - Ask follow-up questions that a human interviewer would naturally ask
           - Probe their thought process, not just their knowledge

        Your response should be a complete conversational turn that includes both acknowledgment and the next question as one natural flow of text.

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

            question_type = result.get("type", "qa")
            if question_type not in ["qa", "scenario", "behavioral", "coding"]:
                logger.warning(
                    f"Invalid question type '{question_type}' received, defaulting to 'qa'"
                )
                question_type = "qa"

            return Question(
                id=question_id,
                text=result.get(
                    "question", "Tell me about your experience with data processing."
                ),
                type=question_type,
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

    def generate_reflection_question(self, state: InterviewState) -> str:
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
                Return the complete conversational response including acknowledgment and reflection question.""",
                    ),
                    (
                        "human",
                        """Based on our wonderful conversation:
                {chat_history}
                
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

            result = reflection_chain.invoke({"chat_history": chat_history})

            return result.content

        except Exception as e:
            logger.error(f"Failed to generate reflection question: {e}")
            return """That was really insightful - I appreciate how you worked through that challenge! As we wrap up our conversation, I'm really curious about your learning journey. 

Looking back at our discussion today - and thinking about your technical interests and goals - what's one area you're excited to dive deeper into or improve? It could be something we touched on today, or perhaps something you've been thinking about lately.

I'd love to hear not just what you want to learn, but also how you're thinking about approaching that growth. What's your plan or strategy for developing in that area?"""
