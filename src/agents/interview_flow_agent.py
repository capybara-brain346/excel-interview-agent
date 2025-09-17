from typing import Dict, Any, Optional
import random
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage

from src.models import AutomationState, InterviewQuestion
from src.questions import EXCEL_QUESTIONS, SCENARIO_QUESTIONS, REFLECTION_QUESTIONS


class InterviewFlowAgent:
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm

    def generate_intro_message(self, state: AutomationState) -> str:
        intro_prompt = """
        You are conducting a mock Excel interview. Generate a professional, welcoming introduction that:
        1. Introduces yourself as an Excel interview assistant
        2. Explains the interview structure (Q&A → Scenario → Reflection → Feedback)
        3. Sets expectations for the candidate
        4. Asks if they're ready to begin
        
        Keep it concise but friendly.
        """

        messages = [
            SystemMessage(content=intro_prompt),
            HumanMessage(
                content="Generate the introduction message for the Excel interview."
            ),
        ]

        response = self.llm.invoke(messages)
        return response.content

    def select_next_question(
        self, state: AutomationState
    ) -> Optional[InterviewQuestion]:
        if state["phase"] == "qa":
            difficulty = state["difficulty_level"]
            available_questions = EXCEL_QUESTIONS.get(difficulty, [])

            if state["q_index"] < len(available_questions):
                return available_questions[state["q_index"]]

        elif state["phase"] == "scenario":
            if state["q_index"] < len(SCENARIO_QUESTIONS):
                return SCENARIO_QUESTIONS[state["q_index"]]

        return None

    def generate_question_prompt(self, question: InterviewQuestion) -> str:
        if question.context:
            return f"""**Context:** {question.context}

**Question:** {question.question_text}

Please provide your answer with as much detail as possible, including specific Excel functions, formulas, or steps you would take."""
        else:
            return f"""**Question:** {question.question_text}

Please provide your answer with as much detail as possible, including specific Excel functions, formulas, or steps you would take."""

    def generate_reflection_prompt(self, state: AutomationState) -> str:
        reflection_question = random.choice(REFLECTION_QUESTIONS)

        prompt = f"""We're now in the reflection phase of the interview. This is your opportunity for self-assessment.

**Reflection Question:** {reflection_question}

Please take a moment to think about your Excel experience and provide an honest self-evaluation."""

        return prompt

    def generate_closing_message(self, state: AutomationState) -> str:
        closing_prompt = f"""
        Generate a professional closing message for the Excel interview that:
        1. Thanks the candidate for their participation
        2. Mentions that feedback will be provided
        3. Encourages continued Excel learning
        4. Maintains a positive, supportive tone
        
        The candidate completed {len(state["responses"])} questions.
        """

        messages = [
            SystemMessage(content=closing_prompt),
            HumanMessage(
                content="Generate the closing message for the Excel interview."
            ),
        ]

        response = self.llm.invoke(messages)
        return response.content

    def process_phase(self, state: AutomationState) -> Dict[str, Any]:
        phase = state["phase"]

        if phase == "intro":
            message = self.generate_intro_message(state)
            return {"message": message, "next_phase": "qa"}

        elif phase == "qa":
            question = self.select_next_question(state)
            if question:
                message = self.generate_question_prompt(question)
                return {
                    "message": message,
                    "current_question": question,
                    "next_phase": "qa",
                }
            else:
                return {
                    "message": "Moving to scenario exercise...",
                    "next_phase": "scenario",
                }

        elif phase == "scenario":
            question = self.select_next_question(state)
            if question:
                message = self.generate_question_prompt(question)
                return {
                    "message": message,
                    "current_question": question,
                    "next_phase": "scenario",
                }
            else:
                return {
                    "message": "Moving to reflection phase...",
                    "next_phase": "reflection",
                }

        elif phase == "reflection":
            message = self.generate_reflection_prompt(state)
            return {"message": message, "next_phase": "closing"}

        elif phase == "closing":
            message = self.generate_closing_message(state)
            return {"message": message, "next_phase": "end"}

        return {"message": "Interview completed.", "next_phase": "end"}
