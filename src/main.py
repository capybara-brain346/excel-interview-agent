import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from src.workflow import ExcelInterviewWorkflow


class ExcelInterviewSystem:
    def __init__(self, google_api_key: str = None):
        load_dotenv()

        if google_api_key:
            os.environ["GOOGLE_API_KEY"] = google_api_key
        elif not os.getenv("GOOGLE_API_KEY"):
            raise ValueError(
                "Google API key must be provided either as parameter or in .env file"
            )

        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)

        self.workflow = ExcelInterviewWorkflow(self.llm)
        self.current_state = None

    def start_interview(self) -> str:
        self.current_state = self.workflow.start_interview()
        return self.workflow.get_current_message(self.current_state)

    def submit_response(self, user_response: str) -> str:
        if not self.current_state:
            raise ValueError("Interview not started. Call start_interview() first.")

        self.current_state = self.workflow.process_user_response(
            self.current_state, user_response
        )

        return self.workflow.get_current_message(self.current_state)

    def is_complete(self) -> bool:
        if not self.current_state:
            return False
        return self.workflow.is_interview_complete(self.current_state)

    def get_feedback_report(self) -> dict:
        if not self.current_state or not self.current_state.get("feedback_report"):
            return None

        report = self.current_state["feedback_report"]
        return {
            "strengths": report.strengths,
            "weaknesses": report.weaknesses,
            "next_steps": report.next_steps,
            "readiness_score": report.readiness_score,
            "overall_summary": report.overall_summary,
        }

    def get_interview_progress(self) -> dict:
        if not self.current_state:
            return {"progress": 0, "phase": "not_started"}

        from .agents.state_manager_agent import StateManagerAgent

        state_manager = StateManagerAgent()
        return state_manager.get_interview_progress(self.current_state)


def run_console_interview():
    print("=== Excel Interview System ===")
    print("Make sure you have set your GOOGLE_API_KEY in the .env file")
    print()

    try:
        interview = ExcelInterviewSystem()

        message = interview.start_interview()
        print("Interviewer:", message)
        print()

        while not interview.is_complete():
            user_input = input("Your response: ").strip()

            if user_input.lower() in ["quit", "exit", "stop"]:
                print("Interview terminated by user.")
                break

            if not user_input:
                print("Please provide a response.")
                continue

            try:
                response = interview.submit_response(user_input)
                print("\nInterviewer:", response)

                progress = interview.get_interview_progress()
                print(
                    f"\nProgress: {progress['progress_percentage']:.0f}% - Phase: {progress['phase']}"
                )
                print("-" * 50)

            except Exception as e:
                print(f"Error processing response: {e}")
                continue

        if interview.is_complete():
            print("\n" + "=" * 50)
            print("INTERVIEW COMPLETE")
            print("=" * 50)

            feedback = interview.get_feedback_report()
            if feedback:
                print("\nOVERALL SUMMARY:")
                print(feedback["overall_summary"])

                print(f"\nREADINESS SCORE: {feedback['readiness_score']}/100")

                print("\nSTRENGTHS:")
                for strength in feedback["strengths"]:
                    print(f"• {strength}")

                print("\nAREAS FOR IMPROVEMENT:")
                for weakness in feedback["weaknesses"]:
                    print(f"• {weakness}")

                print("\nNEXT STEPS:")
                for step in feedback["next_steps"]:
                    print(f"• {step}")

    except ValueError as e:
        print(f"Setup Error: {e}")
        print("Please ensure your GOOGLE_API_KEY is set in the .env file")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--ui":
        from .app import launch_app

        print("🚀 Launching Gradio UI...")
        launch_app()
    else:
        run_console_interview()
