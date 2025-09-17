from typing import Dict, Any, List, Literal
from statistics import mean

from src.models import AutomationState, RubricScore


class StateManagerAgent:
    def __init__(self):
        self.max_qa_questions = 3
        self.max_scenario_questions = 1

    def update_state_after_response(
        self, state: AutomationState, user_response: str, evaluation_score: RubricScore
    ) -> AutomationState:
        updated_state = state.copy()

        updated_state["responses"].append(user_response)
        updated_state["scores"].append(evaluation_score)

        updated_state["conversation_history"].append(
            {"role": "user", "content": user_response}
        )

        return updated_state

    def determine_next_phase(
        self, state: AutomationState
    ) -> Literal["intro", "qa", "scenario", "reflection", "closing"]:
        current_phase = state["phase"]

        if current_phase == "intro":
            return "qa"

        elif current_phase == "qa":
            if state["q_index"] >= self.max_qa_questions:
                return "scenario"
            else:
                return "qa"

        elif current_phase == "scenario":
            if state["q_index"] >= self.max_scenario_questions:
                return "reflection"
            else:
                return "scenario"

        elif current_phase == "reflection":
            return "closing"

        elif current_phase == "closing":
            return "closing"

        return current_phase

    def adjust_difficulty(
        self, state: AutomationState
    ) -> Literal["basic", "intermediate", "advanced"]:
        if len(state["scores"]) < 2:
            return state["difficulty_level"]

        recent_scores = state["scores"][-2:]
        avg_correctness = mean([score.correctness for score in recent_scores])
        avg_clarity = mean([score.explanation_clarity for score in recent_scores])

        overall_avg = (avg_correctness + avg_clarity) / 2

        current_difficulty = state["difficulty_level"]

        if overall_avg >= 4.0 and current_difficulty == "basic":
            return "intermediate"
        elif overall_avg >= 4.5 and current_difficulty == "intermediate":
            return "advanced"
        elif overall_avg <= 2.0 and current_difficulty == "advanced":
            return "intermediate"
        elif overall_avg <= 1.5 and current_difficulty == "intermediate":
            return "basic"

        return current_difficulty

    def advance_question_index(self, state: AutomationState) -> int:
        phase = state["phase"]
        current_index = state["q_index"]

        if phase == "qa":
            if current_index < self.max_qa_questions:
                return current_index + 1
            else:
                return 0

        elif phase == "scenario":
            if current_index < self.max_scenario_questions:
                return current_index + 1
            else:
                return 0

        return current_index

    def should_continue_phase(self, state: AutomationState) -> bool:
        phase = state["phase"]

        if phase == "qa":
            return state["q_index"] < self.max_qa_questions
        elif phase == "scenario":
            return state["q_index"] < self.max_scenario_questions
        elif phase in ["intro", "reflection", "closing"]:
            return False

        return False

    def handle_off_topic_response(
        self, state: AutomationState, response: str
    ) -> Dict[str, Any]:
        if self._is_off_topic(response):
            return {
                "is_off_topic": True,
                "redirect_message": "I notice your response seems to be off-topic. Let's refocus on the Excel question at hand. Could you please provide an answer that addresses the specific Excel functionality being asked about?",
            }

        return {"is_off_topic": False}

    def _is_off_topic(self, response: str) -> bool:
        response_lower = response.lower()

        excel_keywords = [
            "excel",
            "formula",
            "function",
            "cell",
            "worksheet",
            "workbook",
            "pivot",
            "chart",
            "sum",
            "average",
            "vlookup",
            "index",
            "match",
        ]

        has_excel_content = any(keyword in response_lower for keyword in excel_keywords)

        if len(response.split()) < 5:
            return True

        if not has_excel_content and len(response.split()) > 10:
            return True

        return False

    def get_interview_progress(self, state: AutomationState) -> Dict[str, Any]:
        total_questions = (
            self.max_qa_questions + self.max_scenario_questions + 1
        )  # +1 for reflection
        completed_questions = len(state["responses"])

        progress_percentage = min(100, (completed_questions / total_questions) * 100)

        return {
            "phase": state["phase"],
            "completed_questions": completed_questions,
            "total_questions": total_questions,
            "progress_percentage": progress_percentage,
            "current_difficulty": state["difficulty_level"],
        }

    def create_initial_state(self) -> AutomationState:
        return {
            "phase": "intro",
            "q_index": 0,
            "responses": [],
            "scores": [],
            "reflection": None,
            "current_question": None,
            "difficulty_level": "basic",
            "feedback_report": None,
            "conversation_history": [],
        }
