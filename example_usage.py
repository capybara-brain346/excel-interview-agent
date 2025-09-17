#!/usr/bin/env python3

from src.main import ExcelInterviewSystem


def example_programmatic_usage():
    print("=== Programmatic Excel Interview Example ===")
    
    interview = ExcelInterviewSystem()
    
    print("Starting interview...")
    intro_message = interview.start_interview()
    print(f"Interviewer: {intro_message}")
    
    sample_responses = [
        "I'm ready to begin the Excel interview!",
        "I would use the SUM function. The formula would be =SUM(A1:A10) to calculate the total of all values in that range.",
        "I would use =AVERAGE(B1:B20) to calculate the mean of all values in the range B1 through B20.",
        "I would create a pivot table by selecting the data, going to Insert > PivotTable, then dragging Region to Rows, Date to Columns (grouped by month), and Revenue to Values as Sum.",
        "I feel most confident with basic formulas like SUM and AVERAGE. I'd like to improve my knowledge of advanced functions like INDEX/MATCH and array formulas. I learn best through hands-on practice with real datasets."
    ]
    
    for i, response in enumerate(sample_responses):
        if interview.is_complete():
            break
            
        print(f"\nUser Response {i+1}: {response}")
        
        try:
            interviewer_response = interview.submit_response(response)
            print(f"Interviewer: {interviewer_response}")
            
            progress = interview.get_interview_progress()
            print(f"Progress: {progress['progress_percentage']:.0f}% - Phase: {progress['phase']}")
            
        except Exception as e:
            print(f"Error: {e}")
            break
    
    if interview.is_complete():
        print("\n" + "="*50)
        print("FINAL FEEDBACK REPORT")
        print("="*50)
        
        feedback = interview.get_feedback_report()
        if feedback:
            print(f"\nOverall Summary: {feedback['overall_summary']}")
            print(f"Readiness Score: {feedback['readiness_score']}/100")
            
            print("\nStrengths:")
            for strength in feedback['strengths']:
                print(f"  • {strength}")
            
            print("\nAreas for Improvement:")
            for weakness in feedback['weaknesses']:
                print(f"  • {weakness}")
            
            print("\nNext Steps:")
            for step in feedback['next_steps']:
                print(f"  • {step}")


if __name__ == "__main__":
    example_programmatic_usage()
