import gradio as gr
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

    def start_interview(self) -> Tuple[List[List[str]], str, bool, bool]:
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
            )

            welcome_message = self.engine.ask_next()

            chat_history = [["Interviewer", welcome_message]]

            chat_history.append(["You", "I understand"])

            next_response = self.engine.process_response("I understand")
            chat_history.append(["Interviewer", next_response])

            return (chat_history, "", True, False)

        except Exception as e:
            error_msg = f"Failed to start interview: {str(e)}"
            error_chat = [["System", error_msg]]
            return (error_chat, "", False, False)

    def submit_response(
        self, user_message: str, chat_history: List[List[str]]
    ) -> Tuple[List[List[str]], str, bool]:
        if not self.engine:
            return chat_history or [], "", False

        if not user_message.strip():
            return chat_history or [], "", False

        try:
            if chat_history is None:
                chat_history = []

            chat_history.append(["You", user_message])

            response = self.engine.process_response(user_message)

            chat_history.append(["Interviewer", response])

            is_complete = self.engine.is_complete()

            return chat_history, "", is_complete

        except Exception as e:
            error_response = f"Error processing response: {str(e)}"
            chat_history.append(["Interviewer", error_response])
            return chat_history, "", False

    def end_interview_early(
        self, chat_history: List[List[str]]
    ) -> Tuple[List[List[str]], bool]:
        if not self.engine:
            return chat_history or [], False

        try:
            if chat_history is None:
                chat_history = []

            end_message = self.engine.end_early()
            chat_history.append(["System", "[Interview ended early by user]"])
            chat_history.append(["Interviewer", end_message])

            return chat_history, True

        except Exception as e:
            error_msg = f"Error ending interview: {str(e)}"
            chat_history.append(["System", f"[Error ending interview: {error_msg}]"])
            return chat_history, False

    def get_report(self) -> str:
        if not self.engine or not self.engine.is_complete():
            return "Interview not complete"

        try:
            text_report = self.engine.get_text_report()
            return text_report if text_report else "No text report available"

        except Exception as e:
            return f"Error retrieving report: {str(e)}"

    def download_pdf_report(self) -> Optional[str]:
        if not self.engine or not self.engine.is_complete():
            return None

        try:
            pdf_path = self.engine.get_pdf_report_path()
            return pdf_path

        except Exception as e:
            print(f"Error generating PDF report: {str(e)}")
            return None

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
            .report-container {
                max-height: 600px;
                overflow-y: auto;
                padding: 15px;
                border: 1px solid #444;
                border-radius: 8px;
                background-color: #2c3e50 !important;
                color: #ecf0f1 !important;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            .report-container * {
                color: #ecf0f1 !important;
            }
            .report-container h1 {
                color: #ecf0f1 !important;
                border-bottom: 2px solid #f39c12;
                padding-bottom: 10px;
            }
            .report-container h2 {
                color: #bdc3c7 !important;
                margin-top: 25px;
                margin-bottom: 15px;
            }
            .report-container h3 {
                color: #95a5a6 !important;
                margin-top: 20px;
                margin-bottom: 10px;
            }
            .report-container ul {
                margin-left: 20px;
            }
            .report-container li {
                margin-bottom: 5px;
            }
            .report-container strong {
                color: #ecf0f1 !important;
            }
            .report-container em {
                color: #95a5a6 !important;
                font-style: italic;
            }
            .report-container a {
                color: #f39c12 !important;
            }
            """,
        ) as interface:
            gr.Markdown("""
            # 🎯 Technical Interview System
            
            This system will conduct a structured technical interview with automated evaluation.
            Your responses will be evaluated on correctness, design thinking, communication, and production readiness.
            """)

            with gr.Row():
                with gr.Column():
                    with gr.Row():
                        start_btn = gr.Button("Start Interview", variant="primary")

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

                    download_btn = gr.Button(
                        "Download PDF Report",
                        variant="primary",
                        interactive=False,
                        visible=False,
                    )

                    pdf_file_output = gr.File(
                        label="Download PDF Report", visible=False
                    )

            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Interview Report")

                    text_report = gr.Markdown(
                        value="Complete the interview to view your personalized feedback report...",
                        elem_classes=["report-container"],
                    )

            start_btn.click(
                fn=self.start_interview,
                inputs=[],
                outputs=[
                    chatbot,
                    user_input,
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
                outputs=[chatbot, user_input, interview_complete],
            ).then(
                fn=lambda complete: (
                    gr.update(interactive=complete),
                    gr.update(interactive=complete, visible=complete),
                ),
                inputs=[interview_complete],
                outputs=[report_btn, download_btn],
            )

            end_early_btn.click(
                fn=self.end_interview_early,
                inputs=[chatbot],
                outputs=[chatbot, interview_complete],
            ).then(
                fn=lambda complete: (
                    gr.update(interactive=complete),
                    gr.update(interactive=complete, visible=complete),
                ),
                inputs=[interview_complete],
                outputs=[report_btn, download_btn],
            ).then(
                fn=lambda: (gr.update(interactive=False), gr.update(interactive=False)),
                outputs=[submit_btn, end_early_btn],
            )

            report_btn.click(fn=self.get_report, outputs=[text_report]).then(
                fn=lambda: (gr.update(visible=False), gr.update(visible=True)),
                outputs=[report_btn, download_btn],
            )

            download_btn.click(
                fn=self.download_pdf_report,
                outputs=[pdf_file_output],
            ).then(
                fn=lambda: gr.update(visible=True),
                outputs=[pdf_file_output],
            )

            user_input.submit(
                fn=self.submit_response,
                inputs=[user_input, chatbot],
                outputs=[chatbot, user_input, interview_complete],
            ).then(
                fn=lambda complete: (
                    gr.update(interactive=complete),
                    gr.update(interactive=complete, visible=complete),
                ),
                inputs=[interview_complete],
                outputs=[report_btn, download_btn],
            )

        return interface


def create_app() -> gr.Blocks:
    app = InterviewApp()
    return app.create_interface()
