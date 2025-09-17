# Tech spec — Minimal, robust interview engine (Python + Gradio)

Below is a highly detailed technical specification so you can implement a production-quality, maintainable interview system **without external orchestration frameworks**. It’s optimized for your constraints: **pure Python**, **Gradio UI**, local runtime (no backend), and evaluators powered by an LLM + optional deterministic checks.

I’ll cover:

1. Goals & non-goals
2. High-level architecture (textual diagram)
3. Data models (Pydantic)
4. State machine & lifecycle
5. Core classes & APIs (signatures + behavior)
6. LLM prompt templates & JSON output contract
7. Rubric & scoring strategy
8. Gradio UI layout & handlers (detailed)
9. Persistence, reproducibility & auditing
10. Deterministic checks & sandboxing (for code questions)
11. Metrics, tests & QA plan
12. Security, privacy & consent
13. MVP roadmap + extension roadmap
14. Minimal working example (skeleton code)

---

# 1. Goals & non-goals

**Goals**

- Implement a clear interview flow: `intro → qa → scenario → reflection → closing`.
- Capture responses, evaluate them using LLM + deterministic checks, and produce an evidence-based feedback report.
- Minimal dependencies, easy to read, testable code.
- Single-process app served via Gradio.

**Non-goals**

- No multi-instance distributed orchestration.
- No complex multi-agent negotiation or RL loop.
- Not intended for final hiring decisions without human review.

---

# 2. High-level architecture (text)

```
Gradio UI  <-->  Controller (InterviewEngine)
                       |
    ---------------------------------------------------------
    |            |                |                         |
 InterviewFlow  Evaluator     Reporter/Feedback         Persistence (JSON)
 Manager/Agent   (LLM + rules)  (aggregate + format)     (local file store)
```

- `InterviewEngine` orchestrates phases and persists state in-memory (and optionally to disk).
- `Evaluator` implements deterministic checks + LLM evaluator; returns structured evaluation objects.
- `Reporter` consumes evaluations and generates final feedback (text + JSON).
- Gradio calls `engine.ask_next()` and `engine.process_response()`.

---

# 3. Data models (Pydantic)

Use typed models for clarity and validation.

```python
from typing import List, Dict, Optional, Literal
from pydantic import BaseModel
from datetime import datetime

Score = Dict[str, float]  # e.g., {"correctness": 4.0, "communication": 3.5, ...}

class Question(BaseModel):
    id: str
    text: str
    type: Literal["qa","scenario","behavioral","coding"]
    metadata: Dict[str, str] = {}

class ResponseRecord(BaseModel):
    question_id: str
    question_text: str
    answer_text: str
    timestamp: datetime
    evaluator_id: Optional[str] = None  # model/version/prompt
    scores: Optional[Score] = None
    rationale: Optional[str] = None
    deterministic_results: Optional[Dict[str, str]] = None  # e.g., unit test outputs

class InterviewState(BaseModel):
    session_id: str
    phase: Literal["intro","qa","scenario","reflection","closing"]
    q_index: int = 0
    difficulty_level: int = 1
    questions: List[Question] = []
    responses: List[ResponseRecord] = []
    start_time: datetime
    end_time: Optional[datetime] = None
    feedback_report: Optional[Dict] = None
    meta: Dict[str, str] = {}  # e.g., model versions, prompts used
```

---

# 4. State machine & lifecycle

Finite states and transitions:

- `intro` → on `ask_next()` returns welcome message and sets phase `qa`.
- `qa` → loop through questions list; for each user response: evaluate, append record, increment `q_index`. If `q_index >= n` → `scenario`.
- `scenario` → ask scenario question; accept response; evaluate; set `reflection`.
- `reflection` → collect reflection answer -> generate feedback -> move to `closing`.
- `closing` → final state; `feedback_report` present.

Edge cases:

- Off-topic detection: keep a per-question retry limit (e.g., 2) then proceed.
- Early termination: allow user to end interview; generate feedback from current state.
- Timeouts: if desired, enforce per-question time budgets.

---

# 5. Core classes & APIs

Design for testability. All I/O via methods; LLM calls abstracted behind `LLMEvaluator` interface.

## InterviewEngine

```python
class InterviewEngine:
    def __init__(self, questions: List[Question], evaluator: Evaluator, reporter: Reporter, persistence: Persistence=None):
        # sets InterviewState
    def ask_next(self) -> str:
        """Return next assistant message (question or end message)."""
    def process_response(self, user_text: str) -> InterviewState:
        """Process a user response: evaluate, update state, and return updated state."""
    def is_complete(self) -> bool:
        """Return True when phase == 'closing' and feedback generated."""
    def save(self, path: str) -> None:
        """Persist state to JSON (for audit)."""
```

## Evaluator (interface)

```python
class Evaluator:
    def evaluate(self, question: Question, answer_text: str, state: InterviewState) -> ResponseRecord:
        """Return ResponseRecord with scores, rationale, deterministic_results."""
```

- Concrete implementations:

  - `LLMEvaluator` — primary: sends a prompt to LLM and parses JSON.
  - `HybridEvaluator` — runs deterministic checks first (e.g., unit tests for coding), then LLM; combines.

## Reporter

```python
class Reporter:
    def generate_report(self, state: InterviewState) -> Dict:
        """
        Aggregate response records, compute overall scores,
        generate strengths/weaknesses, actionable plan, and return dict.
        """
```

## Persistence

Simple JSON save/load. Keep a revision/version field and timestamps.

---

# 6. LLM prompt templates & JSON output contract

You must avoid asking the LLM to expose chain-of-thought. Ask for structured JSON, small text summaries.

**Prompt schema for evaluation (shortened)**

System + Instruction: You are an objective technical interviewer evaluator. Given the question, the candidate's answer, and the rubric, return a **strict JSON** with the schema below. Do NOT output any additional commentary.

**JSON schema to request:**

```json
{
  "scores": {
    "correctness": 0.0,
    "design": 0.0,
    "communication": 0.0,
    "overall": 0.0
  },
  "rationale": "One-sentence justification (<=40 words).",
  "advice": ["One actionable suggestion per weak area."],
  "evidence": ["short quote from candidate answer (<=20 words)"]
}
```

**Example prompt body:**

```
QUESTION:
{question_text}

CANDIDATE ANSWER:
{answer_text}

RUBRIC:
- correctness (0-5): Is the answer factually correct?
- design (0-5): Shows architecture/tradeoffs?
- communication (0-5): clarity, structure, examples.

Return JSON following the schema exactly.
```

**Parsing & validation**

- Validate JSON; if parsing fails, retry once with a stricter instruction. Log model/version & prompt used as metadata.

---

# 7. Rubric & scoring strategy

Use multi-dimensional scores (0.0–5.0 each). Normalize final score 0–100.

**Base rubric dimensions**

- `correctness` (0–5): factual/technical correctness.
- `design` (0–5): architecture, tradeoffs, alternative considerations.
- `communication` (0–5): clarity, structure, examples.
- `production` (0–5): code quality or production-ready considerations (optional, mainly for coding/designs).

**Weighting example**

- correctness 40%
- design 30%
- communication 20%
- production 10%

**Calibration**

- Keep `evaluator_id` metadata (llm model + prompt hash). Later perform isotonic regression or linear mapping from raw LLM overall -> calibrated human scale using labeled dataset.

---

# 8. Gradio UI layout & handlers (detailed)

Use Gradio `Blocks` (recommended) to build a chat-like flow plus side panel showing progress & interim scores.

**UI Components**

- Chat box (main)
- Left panel: Phase label + progress (q_index / total)
- Right panel: Live evaluation summary (if you want instant feedback on last answer) — optional
- Footer buttons: “End interview early”, “Save session”, “Download report”

**Handler flow**

- On load: call `engine.ask_next()` → shows intro.
- On user message submit:

  1. Call `engine.process_response(user_text)`.
  2. Display engine.get_current_message() (which may be next question or closing message).
  3. If `state.feedback_report` present → show final report, enable "Download JSON" button.

**UX hints**

- Show small spinner when LLM evaluation in progress.
- Keep evaluations optional to show immediately. For candidates, immediate feedback is OK in mock interview but not in live hiring — expose a toggle.

---

# 9. Persistence, reproducibility & auditing

- Always save:

  - `InterviewState` JSON after each question (append-only log file with timestamps).
  - `meta`: model name, prompt hash, timestamp.

- Save LLM raw response alongside parsed JSON for audit.
- When regenerating feedback, use saved `evaluator_id` + prompt version; do not re-evaluate with a newer model unless you intentionally want to re-score.

**File structure example**

```
sessions/
  session_<id>/
    state.json
    responses/
      r_001_raw_llm.json
      r_001_parsed.json
    report.json
```

---

# 10. Deterministic checks & sandboxing

For coding questions, deterministic checks are essential.

- **Approach**:

  - Provide template test harness (pytest-style) that runs candidate code inside a sandbox.
  - Use `subprocess` to run code in a `docker` container OR run in-process with heavy sandboxing (dangerous). For purely local, prefer `subprocess` with `timeout`, `resource` limits.

- **What to capture**:

  - Unit test pass/fail summary
  - Runtime errors & stacktrace
  - Time and memory info

- **Deterministic results** stored in `ResponseRecord.deterministic_results` and used to force scoring floors (e.g., failing tests => correctness ≤ 1).

**Important**: If you choose to allow code execution locally, strongly warn the user that running untrusted code has risks. Consider requiring candidate to paste code but **do not execute** unless you accept the risk.

---

# 11. Metrics, tests & QA plan

**Key metrics**

- Agreement with human raters (Spearman corr) — collect a small labeled dataset.
- Average time per interview & per question.
- LLM latency & cost per evaluation.
- Number of model parsing errors / retries.

**Unit tests**

- `InterviewEngine`:

  - transitions between phases correctly for normal and early termination.
  - state persistence after each question.

- `Evaluator`:

  - given a canned LLM response, parse JSON and populate `ResponseRecord`.
  - deterministic fallback when LLM returns malformed JSON.

- `Reporter`:

  - aggregate calculations produce expected weighted totals.

- Gradio handlers:

  - input/output flows behave as expected (mock engine).

**Integration test**

- Full flow with mocked LLM (deterministic stub) to assert final report shape and contents.

---

# 12. Security, privacy & consent

- **Explicit consent**: on UI start, show a consent checkbox for recording/storing answers. Do not store PII if consent is not given.
- **Local encryption**: optional — encrypt saved JSON files with a passphrase.
- **No network for code execution**: disallow outgoing network calls in sandboxes.
- **LLM data policy**: if using a hosted LLM, explain that responses are sent to provider; give an option to use a local model.

---

# 13. MVP roadmap (4–6 days)

1. Day 1: Implement `InterviewEngine`, simple question bank, basic Gradio UI, and in-memory state.
2. Day 2: Implement `LLMEvaluator` with mock LLM first (return random consistent JSON); wire up to `process_response`.
3. Day 3: Implement `Reporter` to aggregate and generate the feedback JSON + simple text report. Add "Save session".
4. Day 4: Replace mock LLM with real LLM integration (OpenAI/Google/other) and add parsing + retries.
5. Day 5: Add deterministic checks for one coding question (run tests locally via `subprocess` with timeout).
6. Day 6: Add unit tests and basic calibration/deprecation logging.

**Next-phase**

- Add admin UI for calibration (human re-score), multi-rubric support, and scheduled retraining for discriminative models.

---

# 14. Minimal working example (skeleton)

This is a **complete, runnable skeleton** that implements the structure above with a mock LLM evaluator. Replace `mock_llm_evaluate` with your real LLM call.

```python
# file: interview_app.py
from typing import List
import gradio as gr
import uuid
from datetime import datetime
from pydantic import BaseModel
import json
import random

# ---- Pydantic models ----
class Question(BaseModel):
    id: str
    text: str
    type: str = "qa"

class ResponseRecord(BaseModel):
    question_id: str
    question_text: str
    answer_text: str
    timestamp: datetime
    evaluator_id: str = "mock-v0"
    scores: dict = {}
    rationale: str = ""
    deterministic_results: dict = {}

class InterviewState(BaseModel):
    session_id: str
    phase: str = "intro"
    q_index: int = 0
    questions: List[Question] = []
    responses: List[ResponseRecord] = []
    start_time: datetime = datetime.utcnow()
    end_time: datetime = None
    feedback_report: dict = None
    meta: dict = {}

# ---- Basic components ----
def make_questions():
    return [
        Question(id="q1", text="Tell me about a project you are proud of."),
        Question(id="q2", text="How would you optimize a slow SQL query?"),
        Question(id="q3", text="Explain multithreading vs multiprocessing."),
    ]

def mock_llm_evaluate(question_text: str, answer_text: str):
    # returns JSON-like dict (imitate LLM)
    sc = {
        "scores": {
            "correctness": float(random.randint(3,5)),
            "design": float(random.randint(2,5)),
            "communication": float(random.randint(2,5))
        },
        "rationale": "Reason: concise and mostly correct.",
        "advice": ["Add examples", "Explain tradeoffs"],
        "evidence": [answer_text[:40]]
    }
    return sc

class Evaluator:
    def evaluate(self, question: Question, answer_text: str):
        r = mock_llm_evaluate(question.text, answer_text)
        scores = r["scores"]
        overall = (scores["correctness"]*0.4 + scores["design"]*0.3 + scores["communication"]*0.3)
        return {
            "scores": scores,
            "overall": overall,
            "rationale": r["rationale"],
            "advice": r["advice"],
            "evidence": r["evidence"]
        }

class Reporter:
    def generate_report(self, state: InterviewState):
        # aggregate
        if not state.responses:
            return {"message":"No responses"}
        total = sum([resp.scores.get("overall",0) for resp in state.responses if isinstance(resp.scores, dict)])
        avg = total / len(state.responses) if state.responses else 0
        strengths = "Good communication." if avg > 6 else "Needs more depth."
        report = {"avg_score": avg, "strengths": strengths, "responses": [r.dict() for r in state.responses]}
        return report

class InterviewEngine:
    def __init__(self, questions: List[Question]):
        self.state = InterviewState(session_id=str(uuid.uuid4()), questions=questions)
        self.evaluator = Evaluator()
        self.reporter = Reporter()

    def ask_next(self):
        if self.state.phase == "intro":
            self.state.phase = "qa"
            return "Welcome! I'll ask a few technical questions."
        if self.state.phase == "qa":
            if self.state.q_index < len(self.state.questions):
                q = self.state.questions[self.state.q_index]
                return q.text
            else:
                self.state.phase = "reflection"
                return "Reflect: what's one thing you would improve?"
        if self.state.phase == "reflection":
            self.state.phase = "closing"
            return "Thank you — generating report..."
        return "Interview complete."

    def process_response(self, user_text: str):
        if self.state.phase == "qa" and self.state.q_index < len(self.state.questions):
            q = self.state.questions[self.state.q_index]
            eval_result = self.evaluator.evaluate(q, user_text)
            resp = ResponseRecord(
                question_id=q.id,
                question_text=q.text,
                answer_text=user_text,
                timestamp=datetime.utcnow(),
                evaluator_id="mock-v0",
                scores={**eval_result["scores"], "overall": eval_result["overall"]},
                rationale=eval_result["rationale"]
            )
            self.state.responses.append(resp)
            self.state.q_index += 1
            return self.ask_next()
        elif self.state.phase == "reflection":
            self.state.end_time = datetime.utcnow()
            self.state.feedback_report = self.reporter.generate_report(self.state)
            self.state.phase = "closing"
            return "Report ready."
        else:
            return self.ask_next()

    def save(self, path="session.json"):
        with open(path, "w") as f:
            f.write(self.state.json(indent=2, default=str))

# ---- Gradio UI ----
engine = InterviewEngine(make_questions())

def on_submit(user_message, chat_history):
    # Append user message to chat history
    if not chat_history:
        chat_history = []
    chat_history.append(("user", user_message))
    # process
    reply = engine.process_response(user_message)
    # engine.ask_next may be next question or closing
    next_msg = engine.ask_next()
    chat_history.append(("assistant", next_msg))
    if engine.state.feedback_report:
        # attach the JSON report as final message
        chat_history.append(("assistant", json.dumps(engine.state.feedback_report, indent=2)))
    return "", chat_history

with gr.Blocks() as demo:
    gr.Markdown("# Minimal Interview Engine")
    chat = gr.Chatbot()
    txt = gr.Textbox(placeholder="Type your answer and press enter")
    btn = gr.Button("Send")
    btn.click(on_submit, inputs=[txt, chat], outputs=[txt, chat])
demo.launch()
```

**Notes**:

- Replace `mock_llm_evaluate` with your real LLM call (OpenAI/Google/etc.).
- Add proper error handling, retries, and prompt logging before using a hosted LLM.

---

# Final recommendations (brutal, practical)

1. **Start small**: implement `InterviewEngine` + `Evaluator` + `Reporter` with mock LLM first. Confirm the UI/UX works end-to-end.
2. **Make state explicit & typed** (Pydantic). It makes debugging and testing much easier.
3. **Isolate LLM usage**: all LLM interactions should go through a single class so you can log and swap models easily.
4. **Add deterministic checks before trusting LLM** for correctness-critical tasks (coding, fact checks).
5. **Persist everything** to disk for auditability. Include raw LLM outputs and prompt versions.
6. **Human-in-the-loop**: never let a single model verdict be the final hiring action. Store human re-score capabilities in your reporter.

---

If you want I can:

- Convert the skeleton into a more production-ready file layout (tests, requirements, README).
- Provide a set of **ready-to-use LLM prompt templates** for `evaluate` and `generate_report` (tuned for OpenAI or Google models).
- Add a basic deterministic unit-test harness for one coding question (safe local execution).

Which one should I produce next?
