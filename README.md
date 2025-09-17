# Excel Interview Agent

A multi-agent Excel interview system built with LangGraph and LangChain, using Google's Gemini LLM. This system simulates a comprehensive Excel interview with adaptive questioning, rubric-based evaluation, and personalized feedback.

## Features

- **Multi-Phase Interview Structure**: Intro → Adaptive Q&A → Scenario Exercise → Reflection → Feedback
- **Intelligent Question Selection**: Adapts difficulty based on performance
- **Comprehensive Evaluation**: Rule-based + LLM rubric grading across multiple dimensions
- **Personalized Feedback**: Detailed strengths, weaknesses, and next steps
- **State Management**: Tracks progress and maintains interview coherence

## Architecture

The system uses four specialized agents orchestrated by LangGraph:

1. **Interview Flow Agent**: Manages conversation flow and question selection
2. **Evaluation Agent**: Scores responses using predefined rubrics
3. **State Manager Agent**: Tracks progress and handles adaptive difficulty
4. **Feedback Agent**: Generates comprehensive final assessment

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   uv sync
   ```
3. Set up your Google API key:
   ```bash
   cp .env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   ```

## Usage

### Console Interview

Run an interactive console interview:

```bash
python main.py
```

### Programmatic Usage

```python
from src.main import ExcelInterviewSystem

# Initialize the system
interview = ExcelInterviewSystem()

# Start the interview
intro_message = interview.start_interview()
print(intro_message)

# Process user responses
response = interview.submit_response("I'm ready to begin!")
print(response)

# Check if interview is complete
if interview.is_complete():
    feedback = interview.get_feedback_report()
    print(feedback)
```

### Example Usage

See `example_usage.py` for a complete programmatic example with sample responses.

## Evaluation Rubrics

Responses are evaluated across multiple dimensions:

- **Correctness** (1-5): Technical accuracy of Excel concepts and formulas
- **Explanation Clarity** (1-5): How well the response is explained
- **Excel Specificity** (1-5): Use of Excel-specific terminology and functions
- **Problem Solving** (1-5): Systematic approach to scenario exercises

## Question Types

- **Basic**: SUM, AVERAGE, COUNT functions
- **Intermediate**: VLOOKUP, Pivot Tables, IF statements
- **Advanced**: INDEX/MATCH, Array formulas, Data cleaning
- **Scenarios**: Real-world business analysis problems

## Configuration

The system can be customized by modifying:

- `src/questions.py`: Add new questions and scenarios
- `src/agents/`: Modify agent behavior and evaluation criteria
- `src/workflow.py`: Adjust workflow logic and phase transitions

## Requirements

- Python 3.11+
- Google API key for Gemini
- Dependencies listed in `pyproject.toml`

## License

This project is open source. See LICENSE file for details.
