# 📘 API Technical Specification (v2)

_Aligned to Interview Flow → Evaluation → State Manager → Feedback Agents_

---

## 🔹 1. Interview Flow Agent APIs

Handles **5 phases**: `intro → adaptive_qna → scenario → reflection → closing`.

### `POST /api/v1/sessions`

Start a new interview.

- **Request:**
    

```json
{
  "candidateName": "Alice",
  "role": "Finance",
  "difficulty": "Intermediate"
}
```

- **Response:**
    

```json
{
  "sessionId": "sess_1234",
  "phase": "INTRO",
  "introMessage": "Hi Alice, I’m your Excel Mock Interviewer. We’ll go through 5 phases together."
}
```

---

### `GET /api/v1/sessions/:id/next`

Move to next phase/question (flow orchestrator).

- **Response (adaptive Q&A):**
    

```json
{
  "phase": "ADAPTIVE_QNA",
  "question": {
    "id": "q2",
    "text": "Explain when to use INDEX+MATCH instead of VLOOKUP.",
    "type": "conceptual"
  }
}
```

- **Response (scenario):**
    

```json
{
  "phase": "SCENARIO",
  "task": {
    "id": "t1",
    "description": "You have missing region codes in this dataset. Show how you’d clean it.",
    "datasetUrl": "https://s3.amazonaws.com/bucket/uploads/sess_1234-dataset.csv"
  }
}
```

---

### `PATCH /api/v1/sessions/:id/skip`

Handle skipped/irrelevant answer (re-ask or move forward).

- **Response:**
    

```json
{ "status": "resent", "question": {...} }
```

---

## 🔹 2. Evaluation Agent APIs

Grades answers using **rubrics per phase**.

### `POST /api/v1/sessions/:id/responses`

Submit answer and return evaluation.

- **Request:**
    

```json
{
  "questionId": "q2",
  "answerText": "=VLOOKUP(42,Products,3,FALSE)"
}
```

- **Response:**
    

```json
{
  "evaluation": {
    "phase": "ADAPTIVE_QNA",
    "rubric": {
      "correctness": 5,
      "explanation": 3,
      "excel_specificity": 4
    },
    "notes": "Formula correct, but explanation lacked depth."
  }
}
```

---

### `POST /api/v1/sessions/:id/scenario-response`

Submit solution for a scenario exercise.

- **Request:**
    

```json
{
  "taskId": "t1",
  "answerText": "Use IFERROR + VLOOKUP to fill missing region codes",
  "formula": "=IFERROR(VLOOKUP(A2,RegionTable,2,FALSE),\"Unknown\")"
}
```

- **Response:**
    

```json
{
  "evaluation": {
    "phase": "SCENARIO",
    "rubric": {
      "applied_problem_solving": 4,
      "realism": 5,
      "excel_specificity": 5
    },
    "notes": "Good use of IFERROR, but could also mention Power Query."
  }
}
```

---

### `POST /api/v1/sessions/:id/reflection`

Submit self-reflection.

- **Request:**
    

```json
{
  "confidence": 7,
  "strengths": "Formulas",
  "weaknesses": "PivotTables",
  "improvementPlan": "Practice INDEX/MATCH"
}
```

- **Response:**
    

```json
{
  "evaluation": {
    "phase": "REFLECTION",
    "rubric": {
      "self_awareness": 4,
      "realism": 5
    },
    "notes": "Strong awareness of weaknesses."
  }
}
```

---

## 🔹 3. State Manager Agent APIs

Tracks **progress + transitions**.

### `GET /api/v1/sessions/:id`

Fetch full session state.

- **Response:**
    

```json
{
  "sessionId": "sess_1234",
  "phase": "SCENARIO",
  "questionNumber": 3,
  "totalQuestions": 5,
  "progress": { "answered": 2, "remaining": 3 },
  "responses": [
    { "questionId": "q1", "score": 4 },
    { "questionId": "q2", "score": 5 }
  ],
  "difficulty": "Intermediate"
}
```

---

### `PATCH /api/v1/sessions/:id/phase`

Manually move to next phase (admin/reviewer override).

- **Request:**
    

```json
{ "phase": "REFLECTION" }
```

- **Response:**
    

```json
{ "status": "moved", "phase": "REFLECTION" }
```

---

## 🔹 4. Feedback Agent APIs

Generates final report after all phases.

### `POST /api/v1/sessions/:id/report`

Generate final report (system-generated).

- **Response:**
    

```json
{
  "overallScore": 81,
  "strengths": ["Strong with formulas", "Good applied problem-solving"],
  "weaknesses": ["PivotTables need practice"],
  "nextSteps": ["Review INDEX/MATCH", "Practice data cleaning in Power Query"],
  "reportUrl": "https://s3.amazonaws.com/bucket/reports/sess_1234.pdf"
}
```

---

### `GET /api/v1/sessions/:id/report`

Fetch previously generated report.

- **Response:**
    

```json
{
  "sessionId": "sess_1234",
  "overallScore": 81,
  "reportUrl": "https://s3.amazonaws.com/bucket/reports/sess_1234.pdf"
}
```

---

# 🔹 API → Agent Mapping (v2)

- **Interview Flow Agent** → `/sessions`, `/sessions/:id/next`, `/sessions/:id/skip`
    
- **Evaluation Agent** → `/responses`, `/scenario-response`, `/reflection`
    
- **State Manager Agent** → `/sessions/:id`, `/sessions/:id/phase`
    
- **Feedback Agent** → `/report` (POST + GET)
    



