## 1. Goals & Scope

### Goals

- Build an AI-powered mock interviewer for Excel skills.
    
- Support **multi-turn conversations**, **adaptive Q&A**, **scenario tasks**, **reflection**, and **final feedback reports**.
    
- Provide rubric-based grading + summary feedback.
    
- Store all transcripts, evaluations, and reports securely.
    

### Non-Goals (PoC stage)

- Multi-language support.
    
- Massive-scale concurrency (>1000 concurrent interviews).
    
- Complex real-time dashboards (just basic reporting).
    

---

## 2. High-Level Architecture

```
[React Frontend]  <--->  [Express Backend API]  <--->  [PostgreSQL DB]
        |                        |                          |
        |                        |                          |
        |                        v                          |
        |                  [Evaluation Layer]               |
        |                        |                          |
        |                        v                          |
        |                    [LLM Provider]                 |
        |                                                   |
        v                                                   |
   [AWS S3 Storage] <----------------------------------------
         (transcripts, uploaded datasets, generated PDFs)
```

---

## 3. Component Breakdown

### Frontend (React)

- Candidate UI (interview flow, chat, scenario table, reflection form).
    
- Reviewer UI (override rubric scores, publish reports).
    
- REST API calls to Express backend for session mgmt & evaluations.
    
### Backend (Express + TypeScript)

- **API Routes**
    
    - `POST /sessions` → create new session.
        
    - `GET /sessions/:id` → fetch session state.
        
    - `POST /sessions/:id/responses` → submit candidate answer.
        
    - `POST /sessions/:id/evaluate` → run rubric evaluation (rule-based + LLM).
        
    - `GET /sessions/:id/report` → fetch final report.
        
    - `POST /sessions/:id/publish` → mark report as shared.
        
- **Evaluation Layer**
    
    - Rule-based Excel formula checker.
        
    - LLM evaluator (prompt-engineered rubric grader).
        
    - Aggregates rubric scores & stores results.
        
- **Report Generator**
    
    - Creates structured report (JSON + PDF).
        
    - Stores PDF in S3, saves reference in DB.
        
- **Session Manager**
    
    - Tracks current phase, question index, difficulty.
        
    - Emits state updates to frontend via WebSocket.
        

### 🔹 Database (Postgres)

**Schema (simplified)**

- `users` → candidate/reviewer metadata.
    
- `sessions` → id, candidate_id, role, difficulty, status, started_at, ended_at.
    
- `questions` → id, session_id, text, type, expected_answers JSONB.
    
- `responses` → id, question_id, answer_text, rubric JSONB, evaluation_notes.
    
- `reports` → id, session_id, overall_score, feedback JSONB, s3_url.
    
- `events` → (optional) log stream of actions (phase changes, evaluations).
    

### 🔹 Storage (S3)

- Candidate-uploaded datasets (CSV, sanitized).
    
- Generated transcripts & reports (PDF).
    
- File keys linked to session/report IDs in DB.
    

---
Perfect 👍 sticking to **REST** will keep your PoC much simpler and easier to ship.

Here’s how the **system design changes** when we drop WebSockets and just use **HTTP REST (with optional SSE later if needed)**:

---

## 🔹 Updated Data Flow with REST

1. **Candidate starts interview**
    
    - `POST /sessions` → creates session in Postgres.
        
    - Response: `{sessionId, firstQuestion}`.
        
2. **Candidate answers a question**
    
    - `POST /sessions/:id/responses` with `{questionId, answerText}`.
        
    - Backend: saves response, runs evaluation (rule-based + LLM), updates DB.
        
    - Returns **final evaluation in response** (no need for push).
        
3. **Interview flow continues**
    
    - Frontend calls `GET /sessions/:id/next-question`.
        
    - Backend (state manager) decides what to serve:
        
        - Next Q (adaptive Q&A),
            
        - Scenario task,
            
        - Reflection prompt,
            
        - Or closing.
            
4. **Scenario exercise**
    
    - Candidate uploads dataset → `POST /sessions/:id/uploads` → file saved in S3.
        
    - Returns file reference.
        
5. **Reflection**
    
    - `POST /sessions/:id/reflection` → stores candidate’s self-assessment.
        
6. **Feedback report generation**
    
    - `GET /sessions/:id/report` → aggregates all scores + generates feedback.
        
    - Returns structured JSON and S3 link to PDF.
        

---

## 🔹 API Endpoints (REST-First)

### Session Management

```http
POST /api/sessions
{
  "candidateName": "Alice",
  "role": "Finance",
  "difficulty": "Intermediate"
}
→ 201 { "sessionId": "1234", "firstQuestion": {...} }
```

### Answer Submission & Evaluation

```http
POST /api/sessions/1234/responses
{
  "questionId": "q1",
  "answerText": "=VLOOKUP(42,Products,3,FALSE)"
}
→ 200 {
   "evaluation": {
      "correctness": 5,
      "explanation": 3,
      "excel_specificity": 4,
      "notes": "Correct formula, limited reasoning"
   },
   "nextQuestion": {...}
}
```

### File Upload (Scenario)

```http
POST /api/sessions/1234/uploads
(form-data with CSV)
→ 201 { "fileKey": "s3://bucket/uploads/1234-dataset.csv" }
```

### Reflection

```http
POST /api/sessions/1234/reflection
{
  "confidence": 7,
  "strengths": "Formulas",
  "weaknesses": "PivotTables"
}
→ 200 { "status": "saved" }
```

### Final Report

```http
GET /api/sessions/1234/report
→ 200 {
   "overallScore": 82,
   "strengths": [...],
   "weaknesses": [...],
   "nextSteps": [...],
   "reportUrl": "https://s3.amazonaws.com/bucket/reports/1234.pdf"
}
```

---

## 🔹 Pros of REST-only design

- **Simple infra** → just Express + Postgres + S3.
    
- **Deterministic UX** → frontend always fetches the latest state when needed.
    
- **Easier scaling** → stateless requests, works well behind load balancer.
    
- **Logging & monitoring simpler** (every request/response is logged).
    

---

## 🔹 Limitations vs WebSockets

- No live streaming (evaluation results appear only after backend finishes).
    
- No “observer mode” for reviewers in real-time (they’ll have to view after the fact).
    
- More request/response cycles (though manageable at PoC scale).
    

---

✅ For your PoC: **REST-only is the right choice.** It matches your priority: _get something working end-to-end quickly, without fighting infra complexity_.

---

Do you want me to **draft the database schema in SQL (tables + relationships)** next, so it matches this REST flow exactly? That way you’ll see how every API call maps into Postgres rows.
---

## 6. Scaling & Deployment

### Phase 1 (PoC)

- Express backend + Postgres + S3 all in one AWS VPC.
    
- React frontend hosted on Netlify/Vercel.
    
- LLM calls go to OpenAI/Gemini APIs.
    

### Phase 2 (Production Scaling)

- Split services:
    
    - Backend API (Express on ECS).
        
    - Worker service for evaluations (async jobs via SQS).
        
    - Postgres on RDS, S3 for storage.
        
    - Frontend (React/Next.js) on Vercel.
        
- Monitoring: CloudWatch + Grafana for DB/worker metrics.
    

---

## 7. Security & Privacy

- JWT-based auth for reviewers/admins.
    
- Candidate sessions can use anonymous tokens.
    
- File sanitization before S3 storage (strip macros).
    
- Encrypt all S3 objects (AES-256, SSE-S3).
    
- Restrict report sharing (manual publish only).
    
- GDPR-friendly: allow data deletion per candidate.
    

---

## 8. Risks & Mitigations

- **LLM misgrading** → add reviewer override + logs.
    
- **Large file uploads** → limit size, preprocess CSV.
    
- **System downtime** → snapshots of Postgres, retries on S3 upload.
    
- **Cold start** (no dataset) → bootstrap with hand-written Q&A + rule-based checks.
    

---

✅ This design gives you a **clear separation of UI, backend, DB, and storage**, while staying simple enough for a PoC but ready to evolve into production on AWS ECS.

---

Do you want me to **draw this as a proper architecture diagram** (boxes/arrows AWS-style) so you can use it in your design doc or presentation?