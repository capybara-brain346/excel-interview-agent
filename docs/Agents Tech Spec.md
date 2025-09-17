## 1. Overview

The system simulates a **mock Excel interview** using a multi-agent workflow built on **LangGraph**. It manages a structured interview flow, evaluates answers with rubrics, adapts dynamically, and generates constructive feedback.

Workflow Phases:  
**Intro → Adaptive Q&A → Scenario Exercise → Reflection → Closing**

---

## 2. Core Agents

### 2.1 Interview Flow Agent

**Role:** Orchestrates the entire interview, managing the conversation across 5 phases.

- **Inputs:**
    
    - `phase` (intro, qa, scenario, reflection, closing)
        
    - `state` (current question index, progress)
        
- **Outputs:**
    
    - Next **interview prompt** (intro message, Excel question, scenario, reflection question, or closing message).
        
- **Behaviors:**
    
    - Introduce itself and explain the process.
        
    - Selects questions (basic → advanced).
        
    - Injects variety: formulas, pivot tables, data cleaning, charting.
        
    - Moves conversation through phases.
        

---

### 2.2 Evaluation Agent (Rubric Grader)

**Role:** Evaluates candidate responses against predefined rubrics.

- **Inputs:**
    
    - Candidate’s response
        
    - Question metadata (expected formula/concept, difficulty level)
        
- **Outputs:**
    
    - Scores per rubric axis (1–5)
        
    - Evaluator notes
        
- **Rubric Dimensions:**
    
    1. **Correctness** (is it right?)
        
    2. **Explanation Clarity** (how well explained?)
        
    3. **Excel Specificity** (is it truly Excel-based or generic?)
        
    4. _(Scenario-specific)_ Problem-Solving & Application
        
- **Behaviors:**
    
    - Uses **rule-based checks** for formulas.
        
    - Uses **LLM grading** for explanation + specificity.
        
    - Stores results in `state.scores`.
        

---

### 2.3 State Manager Agent

**Role:** Tracks progress, ensures adaptive & coherent interview flow.

- **Inputs:**
    
    - Current `phase`
        
    - `scores` (from Evaluation Agent)
        
    - `responses` (candidate’s answers)
        
- **Outputs:**
    
    - Updates `phase` (intro → qa → scenario → reflection → closing)
        
    - Adjusts difficulty (based on performance)
        
    - Handles interruptions (skipped or off-topic answers)
        
- **Behaviors:**
    
    - Decides next question or phase.
        
    - Maintains persistent memory of responses + grades.
        
    - Ensures interview concludes smoothly.
        

---

### 2.4 Feedback Agent

**Role:** Provides final assessment and constructive guidance.

- **Inputs:**
    
    - Aggregated rubric scores
        
    - Candidate’s self-reflection
        
- **Outputs:**
    
    - Structured feedback report:
        
        - **Strengths**
            
        - **Weaknesses**
            
        - **Next Steps**
            
    - Optional readiness score (0–100).
        
- **Behaviors:**
    
    - Synthesizes evaluation + reflection.
        
    - Personalizes advice (e.g., “focus on PivotTables before advanced charts”).
        
    - Concludes interview with professional closing.
        

---

## 3. LangGraph Workflow

### State Object (`AutomationState`)

```python
class AutomationState(TypedDict):
    phase: str                # intro, qa, scenario, reflection, closing
    q_index: int              # current question index
    responses: List[str]      # candidate answers
    scores: List[Dict]        # rubric results
    reflection: Optional[str] # self-evaluation by candidate
```

### Graph Structure

```
[Interview Flow Agent] → (prompts user)
          ↓
   [Evaluation Agent] → (scores response)
          ↓
   [State Manager Agent] → (updates phase/difficulty)
          ↓
    ┌───────────────┬───────────────┬───────────────┐
    ↓               ↓               ↓
 Adaptive Q&A   Scenario Exercise   Reflection
    └───────────────────────────────┘
          ↓
      [Feedback Agent] → Final Report
          ↓
           END
```

---

## 4. Tech Stack

- **LangGraph** → multi-agent orchestration.
    
- **LLM (OpenAI/Gemini/Anthropic)** → answer evaluation, rubric grading, feedback generation.

- **Typescript**

---

## 5. PoC Scope

- **Questions:** 3–4 adaptive Q&A, 1 scenario, 1 reflection.
    
- **Evaluation:** Rule-based + LLM rubric grading.
    
- **Feedback:** Structured 3-section report.
    
- **State Management:** Minimal but explicit (no long-term memory).
    
