import uuid
import logging
from typing import Optional
from datetime import datetime

from src.interview_engine.models import Question, InterviewState
from src.interview_engine.evaluator import Evaluator
from src.interview_engine.reporter import Reporter
from src.interview_engine.persistence import Persistence
from src.interview_engine.question_generator import QuestionGenerator

logger = logging.getLogger(__name__)


class InterviewEngine:
    def __init__(
        self,
        evaluator: Evaluator,
        question_generator: Optional[QuestionGenerator] = None,
        reporter: Optional[Reporter] = None,
        persistence: Optional[Persistence] = None,
        session_id: Optional[str] = None,
        target_questions: int = 4,
    ):
        self.evaluator = evaluator
        self.question_generator = question_generator or QuestionGenerator()
        self.reporter = reporter or Reporter()
        self.persistence = persistence or Persistence()
        self.target_questions = target_questions

        self.state = InterviewState(
            session_id=session_id or str(uuid.uuid4()),
            phase="intro",
            questions=[],
            start_time=datetime.utcnow(),
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
            if len(self.state.responses) < self.target_questions:
                try:
                    question = self.question_generator.generate_next_question(
                        self.state
                    )
                    self.state.questions.append(question)
                    self._current_message = (
                        f"**Question {len(self.state.responses) + 1}:** {question.text}"
                    )
                    return self._current_message
                except Exception as e:
                    logger.error(f"Failed to generate next question: {e}")
                    self.state.phase = "scenario"
                    return self.ask_next()
            else:
                self.state.phase = "scenario"
                self._current_message = self._get_scenario_question()
                return self._current_message

        elif self.state.phase == "scenario":
            self.state.phase = "reflection"
            self._current_message = self._get_reflection_question()
            return self._current_message

        elif self.state.phase == "reflection":
            self.state.phase = "closing"
            self._current_message = "Thank you for your responses. I'm now generating your feedback report..."
            return self._current_message

        elif self.state.phase == "closing":
            if not self.state.feedback_report:
                self._generate_final_report()
            self._current_message = "Interview complete. Your feedback report is ready!"
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
            return "Error: No question available. Let's continue."

        current_question_index = len(self.state.responses)
        if current_question_index >= len(self.state.questions):
            logger.error("Response index out of bounds")
            return "Error: Response processing issue. Let's continue."

        question = self.state.questions[current_question_index]

        try:
            response_record = self.evaluator.evaluate(question, user_text, self.state)
            self.state.responses.append(response_record)

            self._save_state()

            next_message = self.ask_next()
            return f"Thank you for your response.\n\n{next_message}"

        except Exception as e:
            logger.error(f"Error evaluating response: {e}")
            return "There was an issue evaluating your response. Let's continue to the next question."

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
            return f"Thank you for working through that scenario.\n\n{next_message}"

        except Exception as e:
            logger.error(f"Error evaluating scenario response: {e}")
            return (
                "There was an issue evaluating your response. Let's move to reflection."
            )

    def _process_reflection_response(self, user_text: str) -> str:
        reflection_question = Question(
            id="reflection", text=self._get_reflection_question(), type="behavioral"
        )

        try:
            response_record = self.evaluator.evaluate(
                reflection_question, user_text, self.state
            )
            self.state.responses.append(response_record)

            self.state.end_time = datetime.utcnow()
            self._save_state()

            next_message = self.ask_next()
            return f"Thank you for your reflection.\n\n{next_message}"

        except Exception as e:
            logger.error(f"Error evaluating reflection response: {e}")
            self.state.end_time = datetime.utcnow()
            next_message = self.ask_next()
            return f"Thank you for your reflection.\n\n{next_message}"

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
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _get_intro_message(self) -> str:
        return """Welcome to your technical interview! 

I'll be asking you a series of questions to evaluate your technical knowledge and problem-solving skills. The interview consists of:

1. **Technical Q&A** - Several technical questions
2. **Scenario** - A practical problem-solving scenario  
3. **Reflection** - A brief reflection on your experience

Please answer thoughtfully and feel free to explain your reasoning. Let's begin!"""

    def _get_scenario_question(self) -> str:
        try:
            return self.question_generator.generate_scenario_question(self.state)
        except Exception as e:
            logger.error(f"Failed to generate scenario question: {e}")
            return """**Scenario:** You're working on a web application that has become very slow. Users are complaining about page load times exceeding 10 seconds. 

Walk me through your approach to diagnose and fix this performance issue. What tools would you use, what would you investigate first, and what are some common causes and solutions you'd consider?"""

    def _get_reflection_question(self) -> str:
        try:
            return self.question_generator.generate_reflection_question(self.state)
        except Exception as e:
            logger.error(f"Failed to generate reflection question: {e}")
            return """**Reflection:** Looking back at this interview, what's one technical area you'd like to improve or learn more about? What would be your plan to develop that skill?"""

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
        self.state.end_time = datetime.utcnow()
        self.state.phase = "closing"
        self._generate_final_report()
        return "Interview ended early. Generating feedback report from current responses..."
