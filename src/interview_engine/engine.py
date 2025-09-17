import uuid
import logging
from typing import Optional
from datetime import datetime, timezone

from src.interview_engine.models import Question, InterviewState
from src.interview_engine.reporter import Reporter
from src.interview_engine.evaluator import LLMEvaluator
from src.interview_engine.persistence import Persistence
from src.interview_engine.question_generator import QuestionGenerator

logger = logging.getLogger(__name__)


class InterviewEngine:
    def __init__(
        self,
        evaluator: Optional[LLMEvaluator] = None,
        question_generator: Optional[QuestionGenerator] = None,
        reporter: Optional[Reporter] = None,
        persistence: Optional[Persistence] = None,
        target_questions: int = 4,
    ):
        self.evaluator = evaluator
        self.question_generator = question_generator
        self.reporter = reporter
        self.persistence = persistence
        self.target_questions = target_questions

        self.state = InterviewState(
            session_id=str(uuid.uuid4()),
            phase="intro",
            questions=[],
            start_time=datetime.now(tz=timezone.utc),
            meta={
                "evaluator_type": type(evaluator).__name__,
                "target_questions": str(target_questions),
            },
        )

        self._current_message = ""

    def ask_next(self) -> str:
        if self.state.phase == "intro":
            self._current_message = self._get_intro_message()
            self.state.phase = "qa"
            self._save_state()
            return self._current_message

        elif self.state.phase == "qa":
            elapsed_minutes = self._get_elapsed_minutes()

            if elapsed_minutes >= 15:
                self.state.phase = "closing"
                self._current_message = "I notice we've reached our 15-minute time limit. That wraps up our conversation! I really enjoyed learning about your Excel expertise and approach to problem-solving. I'm putting together your feedback report now - give me just a moment..."
                return self._current_message

            try:
                time_status = self._get_time_status()
                response = self.question_generator.generate_next_response(
                    self.state, time_status
                )

                if response.get("phase_transition"):
                    new_phase = response.get("new_phase")
                    if new_phase in ["reflection", "closing"]:
                        self.state.phase = new_phase
                        if new_phase == "closing":
                            self._generate_final_report()

                self._current_message = response.get(
                    "text", "Let me think of our next question..."
                )
                return self._current_message

            except Exception as e:
                logger.error(f"Failed to generate next response: {e}")
                self._current_message = (
                    "Let me continue with another question about your Excel experience."
                )
                return self._current_message

        elif self.state.phase == "reflection":
            try:
                time_status = self._get_time_status()
                response = self.question_generator.generate_reflection_response(
                    self.state, time_status
                )

                if (
                    response.get("phase_transition")
                    and response.get("new_phase") == "closing"
                ):
                    self.state.phase = "closing"
                    self._generate_final_report()

                self._current_message = response.get(
                    "text", "Thank you for that reflection."
                )
                return self._current_message

            except Exception as e:
                logger.error(f"Failed to generate reflection response: {e}")
                self.state.phase = "closing"
                return self.ask_next()

        elif self.state.phase == "closing":
            if not self.state.feedback_report:
                self._generate_final_report()
            self._current_message = "Perfect! I've finished your personalized feedback report. It includes detailed insights on your responses and some actionable suggestions for your Excel skills development. Thanks for the engaging conversation!"
            return self._current_message

        return "Interview session ended."

    def process_response(self, user_text: str) -> str:
        if not user_text.strip():
            return "Please provide a response to continue."

        try:
            if self.state.phase == "qa" and len(self.state.responses) < len(
                self.state.questions
            ):
                return self._process_qa_response(user_text)

            elif self.state.phase == "scenario":
                return self._process_scenario_response(user_text)

            elif self.state.phase == "reflection":
                return self._process_reflection_response(user_text)

            else:
                return self.ask_next()

        except Exception as e:
            logger.error(f"Error processing response: {e}")
            return "An error occurred while processing your response. Please try again."

    def _process_qa_response(self, user_text: str) -> str:
        if len(self.state.questions) == 0:
            logger.error("No question available for response processing")
            return "Hmm, it looks like we had a technical hiccup. Let me ask you something else."

        current_question_index = len(self.state.responses)
        if current_question_index >= len(self.state.questions):
            logger.error("Response index out of bounds")
            return "Let me think of our next question..."

        question = self.state.questions[current_question_index]

        try:
            response_record = self.evaluator.evaluate(question, user_text, self.state)
            self.state.responses.append(response_record)

            self._save_state()

            next_message = self.ask_next()
            return next_message

        except Exception as e:
            logger.error(f"Error evaluating response: {e}")
            return "I'm having a small technical issue on my end, but let's keep the conversation going with the next question."

    def _process_scenario_response(self, user_text: str) -> str:
        scenario_question = Question(
            id="scenario", text=self._get_scenario_question(), type="scenario"
        )

        try:
            response_record = self.evaluator.evaluate(
                scenario_question, user_text, self.state
            )
            self.state.responses.append(response_record)

            self._save_state()

            next_message = self.ask_next()

            return next_message

        except Exception as e:
            logger.error(f"Error evaluating scenario response: {e}")
            return "I had a small technical issue there, but let's move on to our final reflection question."

    def _process_reflection_response(self, user_text: str) -> str:
        reflection_question = Question(
            id="reflection", text=self._get_reflection_question(), type="behavioral"
        )

        try:
            response_record = self.evaluator.evaluate(
                reflection_question, user_text, self.state
            )
            self.state.responses.append(response_record)

            self.state.end_time = datetime.now(tz=timezone.utc)
            self._save_state()

            next_message = self.ask_next()
            return f"Thank you for sharing that reflection - it's great to hear about your learning goals and growth mindset! {next_message}"

        except Exception as e:
            logger.error(f"Error evaluating reflection response: {e}")
            self.state.end_time = datetime.now(tz=timezone.utc)
            next_message = self.ask_next()
            return f"I really appreciate your thoughtful reflection on the interview. {next_message}"

    def _generate_final_report(self):
        try:
            self.state.feedback_report = self.reporter.generate_report(self.state)

            if self.persistence:
                self.persistence.save_report(
                    self.state.session_id, self.state.feedback_report
                )

            self._save_state()

        except Exception as e:
            logger.error(f"Error generating final report: {e}")
            self.state.feedback_report = {
                "error": "Failed to generate report",
                "session_id": self.state.session_id,
                "timestamp": datetime.datetime.now(
                    tz=datetime.timezone.utc
                ).isoformat(),
            }

    def _get_intro_message(self) -> str:
        return """Hi there! I'm excited to chat with you about your Excel skills and experience. 

This will be a conversational interview where I'll explore your knowledge across different Excel domains like formulas, data analysis, PivotTables, and problem-solving approaches. I'll adapt the conversation based on your responses and decide when we've covered enough ground.

I'm genuinely interested in understanding how you work with Excel and approach data challenges, so please feel free to walk me through your reasoning and share specific examples from your experience.

We have about 15 minutes together, and I'll make sure we cover the key areas efficiently. Ready to get started? Let's dive in!"""

    def _get_scenario_question(self) -> str:
        try:
            return self.question_generator.generate_scenario_question(self.state)
        except Exception as e:
            logger.error(f"Failed to generate scenario question: {e}")
            return """**Scenario:** You're working on a web application that has become very slow. Users are complaining about page load times exceeding 10 seconds. 

Walk me through your approach to diagnose and fix this performance issue. What tools would you use, what would you investigate first, and what are some common causes and solutions you'd consider?"""

    def _get_reflection_question(self) -> str:
        try:
            time_status = self._get_time_status()
            return self.question_generator.generate_reflection_question(
                self.state, time_status
            )
        except Exception as e:
            logger.error(f"Failed to generate reflection question: {e}")
            elapsed_minutes = self._get_elapsed_minutes()
            if elapsed_minutes >= 15:
                return """I notice we've reached our 15-minute time limit, so let's wrap up with a quick reflection. Looking back at our conversation today, what's one technical area you're excited to dive deeper into or improve? What would be your approach to developing in that area?"""
            else:
                return """That was really insightful - I appreciate how you worked through that challenge! As we wrap up our conversation, I'm really curious about your learning journey. Looking back at our discussion today, what's one technical area you're excited to dive deeper into or improve? What would be your plan to develop that skill?"""

    def is_complete(self) -> bool:
        return self.state.phase == "closing" and self.state.feedback_report is not None

    def get_current_message(self) -> str:
        return self._current_message

    def get_feedback_report(self) -> Optional[dict]:
        return self.state.feedback_report

    def get_text_report(self) -> Optional[str]:
        if self.state.feedback_report:
            return self.reporter.format_text_report(self.state.feedback_report)
        return None

    def save(self, path: Optional[str] = None) -> str:
        if path:
            import json

            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.state.model_dump(), f, indent=2, default=str)
            return path
        else:
            return self._save_state()

    def _save_state(self) -> str:
        if self.persistence:
            return self.persistence.save_state(self.state)
        return ""

    def end_early(self) -> str:
        self.state.end_time = datetime.now(tz=timezone.utc)
        self.state.phase = "closing"
        self._generate_final_report()
        return "No problem at all! Thanks for the time we had together. I'll generate a feedback report based on our conversation so far - you've shared some great insights!"

    def _get_elapsed_minutes(self) -> float:
        """Calculate elapsed time since interview start in minutes"""
        current_time = datetime.now(tz=timezone.utc)
        elapsed = current_time - self.state.start_time
        return elapsed.total_seconds() / 60.0

    def _get_time_status(self) -> dict:
        """Get timing information for the interview"""
        elapsed_minutes = self._get_elapsed_minutes()
        remaining_minutes = max(0, 15 - elapsed_minutes)

        return {
            "elapsed_minutes": elapsed_minutes,
            "remaining_minutes": remaining_minutes,
            "time_up": elapsed_minutes >= 15,
            "time_warning": elapsed_minutes >= 12,
        }
