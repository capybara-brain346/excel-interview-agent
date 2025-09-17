### 1. **Structured Interview Flow**

- **Goal:** Simulate a real Excel interview.
    
- **PoC Scope:**
    
    - Intro: agent introduces itself + explains process.
        
    - Questions: 3–5 Excel questions (mixture: formulas, pivot tables, data cleaning).
        
    - Closing: wrap up with a thank-you + transition into feedback.
        
- **Implementation Hint:** Define a simple state machine (`intro → Q&A loop → summary`).
    

---

### 2. **Intelligent Answer Evaluation**

- **Goal:** Assess correctness & depth of Excel answers.
    
- **PoC Scope:**
    
    - Use prompt-engineering + few-shot examples to check answers.
        
    - For formula questions, match against expected formulas (allow variations like `VLOOKUP` vs `INDEX/MATCH`).
        
    - For open-ended questions (“How would you clean this dataset?”), grade along axes: correctness, clarity, Excel-specificity.
        
- **Implementation Hint:** Mix **rule-based checks** (for formulas) with **LLM scoring** (for open text).
    

---

### 3. **Agentic Behavior & State Management**

- **Goal:** Make the agent “think like an interviewer.”
    
- **PoC Scope:**
    
    - Track which question is next, what’s already asked, and user progress.
        
    - Handle simple re-asks if a user skips or gives irrelevant answer.
        
- **Implementation Hint:**
    
    - Use a `state` object (e.g., `phase`, `question_number`, `responses`).
        
    - Frameworks like **LangGraph** or a custom Python class with a loop are enough.
        

---

### 4. **Constructive Feedback Report**

- **Goal:** Give the candidate a useful performance summary.
    
- **PoC Scope:**
    
    - Generate a final summary with **Strengths**, **Weaknesses**, **Next Steps**.
        
    - Tie it back to evaluation results. Example:
        
        - _Strengths:_ Good knowledge of formulas.
            
        - _Weaknesses:_ Needs improvement in pivot tables.
            
        - _Next Steps:_ Practice advanced charting and conditional formatting.
            
- **Implementation Hint:** One LLM call at the end that consumes the evaluation scores + responses.
    

---
 First solution: [[Agentic solution]]