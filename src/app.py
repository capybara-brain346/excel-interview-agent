import gradio as gr
from typing import List, Tuple, Optional

from src.main import ExcelInterviewSystem


class GradioExcelInterviewApp:
    def __init__(self):
        self.interview_system: Optional[ExcelInterviewSystem] = None
        self.interview_started = False

    def initialize_system(self, api_key: str) -> Tuple[str, bool]:
        try:
            if not api_key.strip():
                return "Please enter your Google API key to start the interview.", False

            self.interview_system = ExcelInterviewSystem(google_api_key=api_key)
            message = self.interview_system.start_interview()
            self.interview_started = True

            return message, True

        except Exception as e:
            return f"Error initializing system: {str(e)}", False

    def process_message(
        self, message: str, history: List[Tuple[str, str]]
    ) -> Tuple[List[Tuple[str, str]], str, str, str]:
        if not self.interview_system or not self.interview_started:
            return (
                history,
                "Interview not started. Please initialize with your API key first.",
                "",
                "",
            )

        if not message.strip():
            return history, "Please enter a response.", "", ""

        try:
            response = self.interview_system.submit_response(message)

            history.append((message, response))

            progress_info = self.get_progress_info()
            feedback_info = self.get_feedback_info()

            return history, "", progress_info, feedback_info

        except Exception as e:
            error_msg = f"Error processing response: {str(e)}"
            history.append((message, error_msg))
            return history, "", "", ""

    def get_progress_info(self) -> str:
        if not self.interview_system:
            return "No progress available"

        try:
            progress = self.interview_system.get_interview_progress()
            phase = progress.get("phase", "unknown")
            percentage = progress.get("progress_percentage", 0)

            phase_descriptions = {
                "intro": "Introduction",
                "qa": "Q&A Session",
                "scenario": "Scenario Exercise",
                "reflection": "Reflection",
                "closing": "Closing & Feedback",
            }

            phase_name = phase_descriptions.get(phase, phase.title())

            return f"**Current Phase:** {phase_name}\n**Progress:** {percentage:.0f}%"

        except Exception as e:
            return f"Progress unavailable: {str(e)}"

    def get_feedback_info(self) -> str:
        if not self.interview_system:
            return ""

        try:
            if self.interview_system.is_complete():
                feedback = self.interview_system.get_feedback_report()
                if feedback:
                    feedback_text = f"""
## Interview Complete! 🎉

### Overall Summary
{feedback["overall_summary"]}

### Readiness Score: {feedback["readiness_score"]}/100

### Strengths ✅
{chr(10).join([f"• {strength}" for strength in feedback["strengths"]])}

### Areas for Improvement 📈
{chr(10).join([f"• {weakness}" for weakness in feedback["weaknesses"]])}

### Next Steps 🎯
{chr(10).join([f"• {step}" for step in feedback["next_steps"]])}
"""
                    return feedback_text
            return ""

        except Exception as e:
            return f"Feedback unavailable: {str(e)}"

    def reset_interview(self) -> Tuple[List, str, str, str, str]:
        self.interview_system = None
        self.interview_started = False
        return [], "", "", "", ""


def create_gradio_interface():
    app = GradioExcelInterviewApp()

    with gr.Blocks(title="Excel Interview Agent", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 📊 Excel Interview Agent
        
        Welcome to the AI-powered Excel interview system! This interactive agent will conduct a comprehensive Excel interview with adaptive questioning, real-time evaluation, and personalized feedback.
        
        **Interview Structure:**
        1. **Introduction** - Getting to know you
        2. **Q&A Session** - Adaptive Excel questions 
        3. **Scenario Exercise** - Real-world problem solving
        4. **Reflection** - Self-assessment
        5. **Closing & Feedback** - Comprehensive evaluation
        """)

        with gr.Row():
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(
                    label="Interview Conversation",
                    height=500,
                    show_label=True,
                    container=True,
                    show_copy_button=True,
                )

                with gr.Row():
                    msg = gr.Textbox(
                        label="Your Response",
                        placeholder="Type your response here...",
                        lines=2,
                        max_lines=5,
                        show_label=True,
                        scale=4,
                    )
                    send_btn = gr.Button("Send", variant="primary", scale=1)

                with gr.Row():
                    with gr.Column(scale=1):
                        api_key_input = gr.Textbox(
                            label="Google API Key",
                            placeholder="Enter your Google API key to start...",
                            type="password",
                            show_label=True,
                        )
                    with gr.Column(scale=1):
                        start_btn = gr.Button("Start Interview", variant="primary")
                        reset_btn = gr.Button("Reset Interview", variant="secondary")

            with gr.Column(scale=1):
                progress_display = gr.Markdown(
                    label="Interview Progress",
                    value="Interview not started",
                    show_label=True,
                )

                feedback_display = gr.Markdown(
                    label="Feedback Report",
                    value="Feedback will appear when interview is complete",
                    show_label=True,
                )

        init_status = gr.Textbox(visible=False)

        def start_interview(api_key):
            message, success = app.initialize_system(api_key)
            if success:
                initial_history = [("System", message)]
                progress_info = app.get_progress_info()
                return initial_history, "", progress_info, "", message
            else:
                return [], "", "", "", message

        def handle_message(message, history):
            new_history, cleared_msg, progress_info, feedback_info = (
                app.process_message(message, history)
            )
            return new_history, cleared_msg, progress_info, feedback_info

        def reset_all():
            return app.reset_interview()

        start_btn.click(
            fn=start_interview,
            inputs=[api_key_input],
            outputs=[chatbot, msg, progress_display, feedback_display, init_status],
        )

        send_btn.click(
            fn=handle_message,
            inputs=[msg, chatbot],
            outputs=[chatbot, msg, progress_display, feedback_display],
        )

        msg.submit(
            fn=handle_message,
            inputs=[msg, chatbot],
            outputs=[chatbot, msg, progress_display, feedback_display],
        )

        reset_btn.click(
            fn=reset_all,
            outputs=[chatbot, msg, progress_display, feedback_display, api_key_input],
        )

        gr.Markdown("""
        ### Instructions:
        1. Enter your Google API key in the field above
        2. Click "Start Interview" to begin
        3. Respond to the interviewer's questions in the text box
        4. Monitor your progress in the right panel
        5. View your comprehensive feedback report when complete
        
        ### Tips:
        - Be specific about Excel functions and formulas
        - Explain your reasoning clearly
        - Don't hesitate to mention alternative approaches
        - The system adapts to your skill level automatically
        """)

    return demo


def launch_app(
    share: bool = False, server_name: str = "127.0.0.1", server_port: int = 7860
):
    demo = create_gradio_interface()
    demo.launch(
        share=share, server_name=server_name, server_port=server_port, show_error=True
    )


if __name__ == "__main__":
    launch_app()
