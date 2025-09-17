import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from src.interview_engine.models import Question, ResponseRecord, InterviewState

logger = logging.getLogger(__name__)


class LLMEvaluator:
    def __init__(self, model_name: str = "gemini-2.5-flash", temperature: float = 0.1):
        self.model_name = model_name
        self.temperature = temperature
        self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=temperature)

        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", self._get_system_prompt()),
                ("human", self._get_evaluation_prompt()),
            ]
        )

        self.parser = JsonOutputParser()
        self.chain = self.prompt_template | self.llm | self.parser

    def _get_system_prompt(self) -> str:
        return """
        <system_prompt>
        <role>
            <primary_function>objective technical interviewer evaluator</primary_function>
            <evaluation_task>assess candidate answers against provided rubric</evaluation_task>
        </role>

        <input_requirements>
            <required_elements>
            <element>interview question</element>
            <element>candidate's answer</element>
            <element>evaluation rubric</element>
            </required_elements>
        </input_requirements>

        <output_format>
            <format_type>strict JSON only</format_type>
            <restrictions>
            <restriction>NO additional commentary outside JSON</restriction>
            <restriction>NO explanatory text</restriction>
            <restriction>MUST follow exact schema provided</restriction>
            </restrictions>
            
            <json_schema>
            <structure>
                {{
                "scores": {{
                    "correctness": 0.0,
                    "design": 0.0,
                    "communication": 0.0,
                    "production": 0.0,
                    "overall": 0.0
                }},
                "rationale": "One-sentence justification (<=40 words).",
                "advice": ["One actionable suggestion per weak area."],
                "evidence": ["short quote from candidate answer (<=20 words)"]
                }}
            </structure>
            
            <field_constraints>
                <scores>
                <data_type>numeric (float)</data_type>
                <range>0.0 to maximum per rubric</range>
                </scores>
                <rationale>
                <format>single sentence</format>
                <word_limit>40 words maximum</word_limit>
                </rationale>
                <advice>
                <format>array of strings</format>
                <content>one actionable suggestion per identified weak area</content>
                </advice>
                <evidence>
                <format>array of strings</format>
                <content>direct quotes from candidate answer</content>
                <word_limit>20 words maximum per quote</word_limit>
                </evidence>
            </field_constraints>
            </json_schema>
        </output_format>

        <evaluation_instructions>
            <assessment_approach>objective and rubric-based</assessment_approach>
            <scoring_method>align scores with provided rubric criteria</scoring_method>
            <evidence_selection>extract relevant quotes supporting evaluation</evidence_selection>
        </evaluation_instructions>
        </system_prompt>
        """

    def _get_evaluation_prompt(self) -> str:
        return """
        <system_prompt>
        <role>
            <primary_function>objective technical interviewer evaluator</primary_function>
            <evaluation_task>assess candidate answers against provided rubric</evaluation_task>
        </role>

        <input_structure>
            <question_section>
            <label>QUESTION:</label>
            <content>{question_text}</content>
            </question_section>
            <answer_section>
            <label>CANDIDATE ANSWER:</label>
            <content>{answer_text}</content>
            </answer_section>
        </input_structure>

        <evaluation_rubric>
            <scoring_dimensions>
            <dimension name="correctness" range="0-5">
                <criteria>Is the answer factually correct and technically accurate?</criteria>
            </dimension>
            <dimension name="design" range="0-5">
                <criteria>Shows architecture understanding, tradeoffs, and system thinking?</criteria>
            </dimension>
            <dimension name="communication" range="0-5">
                <criteria>Clarity, structure, examples, and explanation quality.</criteria>
            </dimension>
            <dimension name="production" range="0-5">
                <criteria>Code quality, scalability, maintainability considerations.</criteria>
            </dimension>
            </scoring_dimensions>

            <overall_calculation>
            <formula>correctness*0.4 + design*0.3 + communication*0.2 + production*0.1</formula>
            <method>weighted average</method>
            </overall_calculation>
        </evaluation_rubric>

        <special_handling>
            <inadequate_responses>
            <triggers>
                <trigger>"no", "yes", "I don't know"</trigger>
                <trigger>very short non-answers</trigger>
                <trigger>one-word responses</trigger>
                <trigger>minimal responses that don't address the question</trigger>
            </triggers>
            <scoring_protocol>
                <score_range>0.5-1.0 across all dimensions</score_range>
                <rationale_approach>indicate more detail is needed, not false encouragement</rationale_approach>
            </scoring_protocol>
            </inadequate_responses>
        </special_handling>

        <output_format>
            <format_type>strict JSON only</format_type>
            <restrictions>
            <restriction>NO additional commentary outside JSON</restriction>
            <restriction>NO explanatory text</restriction>
            <restriction>MUST follow exact schema provided</restriction>
            </restrictions>
            
            <json_schema>
            <structure>
                {{
                "scores": {{
                    "correctness": 0.0,
                    "design": 0.0,
                    "communication": 0.0,
                    "production": 0.0,
                    "overall": 0.0
                }},
                "rationale": "One-sentence justification (<=40 words).",
                "advice": ["One actionable suggestion per weak area."],
                "evidence": ["short quote from candidate answer (<=20 words)"]
                }}
            </structure>
            
            <field_constraints>
                <scores>
                <data_type>numeric (float)</data_type>
                <range>0.0 to 5.0 per dimension</range>
                </scores>
                <rationale>
                <format>single sentence</format>
                <word_limit>40 words maximum</word_limit>
                </rationale>
                <advice>
                <format>array of strings</format>
                <content>one actionable suggestion per identified weak area</content>
                </advice>
                <evidence>
                <format>array of strings</format>
                <content>direct quotes from candidate answer</content>
                <word_limit>20 words maximum per quote</word_limit>
                </evidence>
            </field_constraints>
            </json_schema>
        </output_format>

        <evaluation_instructions>
            <assessment_approach>objective and rubric-based</assessment_approach>
            <scoring_method>align scores with provided rubric criteria</scoring_method>
            <evidence_selection>extract relevant quotes supporting evaluation</evidence_selection>
            <final_instruction>Return JSON following the schema exactly.</final_instruction>
        </evaluation_instructions>
        </system_prompt>
        """

    def _get_evaluator_id(self) -> str:
        prompt_hash = hashlib.md5(
            (self._get_system_prompt() + self._get_evaluation_prompt()).encode()
        ).hexdigest()[:8]
        return f"{self.model_name}-{prompt_hash}"

    def evaluate(
        self, question: Question, answer_text: str, state: InterviewState
    ) -> ResponseRecord:
        try:
            result = self.chain.invoke(
                {"question_text": question.text, "answer_text": answer_text}
            )

            scores = result.get("scores", {})
            if "overall" not in scores:
                scores["overall"] = self._calculate_overall_score(scores)

            return ResponseRecord(
                question_id=question.id,
                question_text=question.text,
                answer_text=answer_text,
                timestamp=datetime.now(tz=timezone.utc),
                evaluator_id=self._get_evaluator_id(),
                scores=scores,
                rationale=result.get("rationale", ""),
                deterministic_results={},
            )

        except Exception as e:
            logger.error(f"LLM evaluation failed: {e}")
            return self._create_fallback_response(question, answer_text, str(e))

    def _calculate_overall_score(self, scores: Dict[str, float]) -> float:
        weights = {
            "correctness": 0.4,
            "design": 0.3,
            "communication": 0.2,
            "production": 0.1,
        }

        total = 0.0
        for dimension, weight in weights.items():
            total += scores.get(dimension, 0.0) * weight

        return total

    def _create_fallback_response(
        self, question: Question, answer_text: str, error: str
    ) -> ResponseRecord:
        return ResponseRecord(
            question_id=question.id,
            question_text=question.text,
            answer_text=answer_text,
            timestamp=datetime.now(tz=timezone.utc),
            evaluator_id=f"{self._get_evaluator_id()}-fallback",
            scores={
                "correctness": 2.5,
                "design": 2.5,
                "communication": 2.5,
                "production": 2.5,
                "overall": 2.5,
            },
            rationale=f"Evaluation failed, using fallback scores. Error: {error}",
            deterministic_results={"error": error},
        )
