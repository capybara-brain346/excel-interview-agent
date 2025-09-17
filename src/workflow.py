from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI

from src.models import AutomationState
from src.agents.interview_flow_agent import InterviewFlowAgent
from src.agents.evaluation_agent import EvaluationAgent
from src.agents.state_manager_agent import StateManagerAgent
from src.agents.feedback_agent import FeedbackAgent


class ExcelInterviewWorkflow:
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
        self.interview_flow_agent = InterviewFlowAgent(llm)
        self.evaluation_agent = EvaluationAgent(llm)
        self.state_manager_agent = StateManagerAgent()
        self.feedback_agent = FeedbackAgent(llm)

        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        workflow = StateGraph(AutomationState)

        workflow.add_node("interview_flow", self._interview_flow_node)
        workflow.add_node("evaluation", self._evaluation_node)
        workflow.add_node("state_management", self._state_management_node)
        workflow.add_node("feedback_generation", self._feedback_generation_node)

        workflow.set_entry_point("interview_flow")

        workflow.add_conditional_edges(
            "interview_flow",
            self._should_continue_interview,
            {"continue": "evaluation", "end": END},
        )

        workflow.add_edge("evaluation", "state_management")

        workflow.add_conditional_edges(
            "state_management",
            self._determine_next_step,
            {
                "continue_interview": "interview_flow",
                "generate_feedback": "feedback_generation",
                "end": END,
            },
        )

        workflow.add_edge("feedback_generation", END)

        return workflow.compile()

    def _interview_flow_node(self, state: AutomationState) -> Dict[str, Any]:
        result = self.interview_flow_agent.process_phase(state)

        updated_state = {
            **state,
            "conversation_history": [
                *state["conversation_history"],
                {"role": "assistant", "content": result["message"]},
            ],
        }

        if "current_question" in result:
            updated_state["current_question"] = result["current_question"]

        if "next_phase" in result and result["next_phase"] != state["phase"]:
            updated_state["phase"] = result["next_phase"]
            if result["next_phase"] in ["scenario", "reflection"]:
                updated_state["q_index"] = 0

        updated_state["_interview_message"] = result["message"]
        updated_state["_next_phase"] = result.get("next_phase", state["phase"])

        return updated_state

    def _evaluation_node(self, state: AutomationState) -> Dict[str, Any]:
        if not state.get("_user_response"):
            return state

        user_response = state["_user_response"]
        current_question = state.get("current_question")

        if current_question:
            evaluation_score = self.evaluation_agent.evaluate_response(
                user_response, current_question
            )

            updated_state = self.state_manager_agent.update_state_after_response(
                state, user_response, evaluation_score
            )

            updated_state["_evaluation_complete"] = True
            return updated_state

        return state

    def _state_management_node(self, state: AutomationState) -> Dict[str, Any]:
        next_phase = self.state_manager_agent.determine_next_phase(state)
        new_difficulty = self.state_manager_agent.adjust_difficulty(state)

        updated_state = {
            **state,
            "phase": next_phase,
            "difficulty_level": new_difficulty,
        }

        if self.state_manager_agent.should_continue_phase(state):
            updated_state["q_index"] = self.state_manager_agent.advance_question_index(
                state
            )
        else:
            updated_state["q_index"] = 0

        off_topic_check = self.state_manager_agent.handle_off_topic_response(
            state, state.get("_user_response", "")
        )

        if off_topic_check["is_off_topic"]:
            updated_state["_redirect_message"] = off_topic_check["redirect_message"]

        updated_state["_state_updated"] = True
        return updated_state

    def _feedback_generation_node(self, state: AutomationState) -> Dict[str, Any]:
        feedback_report = self.feedback_agent.generate_feedback_report(state)

        return {
            **state,
            "feedback_report": feedback_report,
            "_feedback_generated": True,
        }

    def _should_continue_interview(
        self, state: AutomationState
    ) -> Literal["continue", "end"]:
        if state["phase"] == "closing":
            return "end"
        elif state["phase"] == "intro":
            return "continue" if state.get("_user_response") else "end"
        elif state.get("current_question"):
            return "continue"
        else:
            return "end"

    def _determine_next_step(
        self, state: AutomationState
    ) -> Literal["continue_interview", "generate_feedback", "end"]:
        if state.get("_redirect_message"):
            return "continue_interview"

        if state["phase"] == "closing":
            return "generate_feedback"
        elif state["phase"] in [
            "qa",
            "scenario",
        ] and self.state_manager_agent.should_continue_phase(state):
            return "continue_interview"
        elif state["phase"] == "reflection" and not state.get("reflection"):
            return "continue_interview"
        else:
            return "continue_interview"

    def start_interview(self) -> AutomationState:
        initial_state = self.state_manager_agent.create_initial_state()
        result = self.workflow.invoke(initial_state)
        return result

    def process_user_response(
        self, state: AutomationState, user_response: str
    ) -> AutomationState:
        if state["phase"] == "reflection" and not state.get("reflection"):
            state = {**state, "reflection": user_response}

        updated_state = {**state, "_user_response": user_response}
        result = self.workflow.invoke(updated_state)

        if "_user_response" in result:
            del result["_user_response"]
        if "_evaluation_complete" in result:
            del result["_evaluation_complete"]
        if "_state_updated" in result:
            del result["_state_updated"]
        if "_feedback_generated" in result:
            del result["_feedback_generated"]

        return result

    def get_current_message(self, state: AutomationState) -> str:
        if state.get("_redirect_message"):
            return state["_redirect_message"]
        elif state.get("_interview_message"):
            return state["_interview_message"]
        elif state.get("conversation_history"):
            return state["conversation_history"][-1].get("content", "")
        else:
            return "Welcome to the Excel interview!"

    def is_interview_complete(self, state: AutomationState) -> bool:
        return state["phase"] == "closing" and state.get("feedback_report") is not None
