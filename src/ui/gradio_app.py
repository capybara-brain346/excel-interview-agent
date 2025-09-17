import gradio as gr
import json
from typing import List, Tuple, Optional

from src.interview_engine import (
    InterviewEngine,
    LLMEvaluator,
    Reporter,
    Persistence,
    QuestionGenerator,
)


class InterviewApp:
    def __init__(self):
        self.engine: Optional[InterviewEngine] = None

    def start_interview(
        self, consent_given: bool, use_llm: bool
    ) -> Tuple[List[List[str]], str, str, bool, bool]:
        if not consent_given:
            error_chat = [
                [
                    "System",
                    "Please provide consent to record and evaluate your responses before starting the interview.",
                ]
            ]
            return (
                error_chat,
                "",
                "Not Started",
                False,
                False,
            )

        try:
            evaluator = LLMEvaluator()
            question_generator = QuestionGenerator()
            reporter = Reporter()
            persistence = Persistence()

            self.engine = InterviewEngine(
                evaluator=evaluator,
                question_generator=question_generator,
                reporter=reporter,
                persistence=persistence,
                target_questions=4,
            )

            welcome_message = self.engine.ask_next()
            progress = f"Phase: {self.engine.state.phase.title()} | Questions: 0/{self.engine.target_questions}"

            chat_history = [["Interviewer", welcome_message]]

            return (chat_history, "", progress, True, False)

        except Exception as e:
            error_msg = f"Failed to start interview: {str(e)}"
            error_chat = [["System", error_msg]]
            return (error_chat, "", "Error", False, False)

    def submit_response(
        self, user_message: str, chat_history: List[List[str]]
    ) -> Tuple[List[List[str]], str, str, bool]:
        if not self.engine:
            return chat_history or [], "", "No active interview", False

        if not user_message.strip():
            return chat_history or [], "", self._get_progress_text(), False

        try:
            if chat_history is None:
                chat_history = []

            chat_history.append(["You", user_message])

            response = self.engine.process_response(user_message)

            chat_history.append(["Interviewer", response])

            progress = self._get_progress_text()
            is_complete = self.engine.is_complete()

            return chat_history, "", progress, is_complete

        except Exception as e:
            error_response = f"Error processing response: {str(e)}"
            chat_history.append(["Interviewer", error_response])
            return chat_history, "", self._get_progress_text(), False

    def end_interview_early(
        self, chat_history: List[List[str]]
    ) -> Tuple[List[List[str]], str, bool]:
        if not self.engine:
            return chat_history or [], "No active interview", False

        try:
            if chat_history is None:
                chat_history = []

            end_message = self.engine.end_early()
            chat_history.append(["System", "[Interview ended early by user]"])
            chat_history.append(["Interviewer", end_message])

            progress = self._get_progress_text()
            return chat_history, progress, True

        except Exception as e:
            error_msg = f"Error ending interview: {str(e)}"
            chat_history.append(["System", f"[Error ending interview: {error_msg}]"])
            return chat_history, self._get_progress_text(), False

    def get_report(self) -> Tuple[str, str]:
        if not self.engine or not self.engine.is_complete():
            return "Interview not complete", ""

        try:
            report = self.engine.get_feedback_report()
            text_report = self.engine.get_text_report()

            json_report = (
                json.dumps(report, indent=2, default=str)
                if report
                else "No report available"
            )
            text_display = text_report if text_report else "No text report available"

            return text_display, json_report

        except Exception as e:
            error_msg = f"Error retrieving report: {str(e)}"
            return error_msg, error_msg

    def _get_progress_text(self) -> str:
        if not self.engine:
            return "No active interview"

        phase = self.engine.state.phase.title()
        q_num = len(self.engine.state.responses)
        total_q = self.engine.target_questions + 2

        return f"Phase: {phase} | Responses: {q_num}/{total_q}"

    def create_interface(self) -> gr.Blocks:
        with gr.Blocks(
            title="Technical Interview System",
            theme=gr.themes.Soft(),
            css="""
            .gradio-container {
                max-width: 1200px;
                margin: auto;
            }
            .chat-container {
                height: 500px;
            }
            """,
        ) as interface:
            gr.Markdown("""
            # 🎯 Technical Interview System
            
            This system will conduct a structured technical interview with automated evaluation.
            Your responses will be evaluated on correctness, design thinking, communication, and production readiness.
            """)

            with gr.Row():
                with gr.Column(scale=2):
                    consent_checkbox = gr.Checkbox(
                        label="I consent to having my responses recorded and evaluated for this interview",
                        value=False,
                    )

                    with gr.Row():
                        use_llm_checkbox = gr.Checkbox(
                            label="Use LLM Evaluator (requires API key)", value=False
                        )

                        start_btn = gr.Button("Start Interview", variant="primary")

                with gr.Column(scale=1):
                    progress_text = gr.Textbox(
                        label="Progress", value="Not Started", interactive=False
                    )

            with gr.Row():
                with gr.Column(scale=3):
                    chatbot = gr.Chatbot(
                        label="Interview Chat", height=500, show_label=True
                    )

                    with gr.Row():
                        user_input = gr.Textbox(
                            label="Your Response",
                            placeholder="Type your answer here...",
                            lines=3,
                            max_lines=10,
                        )

                    with gr.Row():
                        submit_btn = gr.Button("Submit Response", variant="primary")
                        end_early_btn = gr.Button(
                            "End Interview Early", variant="secondary"
                        )

                with gr.Column(scale=1):
                    gr.Markdown("### Interview Status")

                    interview_active = gr.State(False)
                    interview_complete = gr.State(False)

                    report_btn = gr.Button(
                        "Get Report", variant="secondary", interactive=False
                    )

            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Interview Report")

                    with gr.Tabs():
                        with gr.Tab("Text Report"):
                            text_report = gr.Textbox(
                                label="Formatted Report",
                                lines=20,
                                max_lines=30,
                                interactive=False,
                            )

                        with gr.Tab("JSON Report"):
                            json_report = gr.Textbox(
                                label="Detailed JSON Report",
                                lines=20,
                                max_lines=30,
                                interactive=False,
                            )

            start_btn.click(
                fn=self.start_interview,
                inputs=[consent_checkbox, use_llm_checkbox],
                outputs=[
                    chatbot,
                    user_input,
                    progress_text,
                    interview_active,
                    interview_complete,
                ],
            ).then(
                fn=lambda active: gr.update(interactive=active),
                inputs=[interview_active],
                outputs=[submit_btn],
            ).then(
                fn=lambda active: gr.update(interactive=active),
                inputs=[interview_active],
                outputs=[end_early_btn],
            )

            submit_btn.click(
                fn=self.submit_response,
                inputs=[user_input, chatbot],
                outputs=[chatbot, user_input, progress_text, interview_complete],
            ).then(
                fn=lambda complete: gr.update(interactive=complete),
                inputs=[interview_complete],
                outputs=[report_btn],
            )

            end_early_btn.click(
                fn=self.end_interview_early,
                inputs=[chatbot],
                outputs=[chatbot, progress_text, interview_complete],
            ).then(
                fn=lambda complete: gr.update(interactive=complete),
                inputs=[interview_complete],
                outputs=[report_btn],
            ).then(
                fn=lambda: (gr.update(interactive=False), gr.update(interactive=False)),
                outputs=[submit_btn, end_early_btn],
            )

            report_btn.click(fn=self.get_report, outputs=[text_report, json_report])

            user_input.submit(
                fn=self.submit_response,
                inputs=[user_input, chatbot],
                outputs=[chatbot, user_input, progress_text, interview_complete],
            ).then(
                fn=lambda complete: gr.update(interactive=complete),
                inputs=[interview_complete],
                outputs=[report_btn],
            )

        return interface


def create_app() -> gr.Blocks:
    app = InterviewApp()
    return app.create_interface()
