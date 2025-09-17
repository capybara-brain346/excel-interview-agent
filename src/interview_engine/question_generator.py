import logging
from datetime import datetime, timezone

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from src.interview_engine.models import Question, InterviewState

logger = logging.getLogger(__name__)


class QuestionGenerator:
    def __init__(self, model_name: str = "gemini-2.5-flash", temperature: float = 0.3):
        self.model_name = model_name
        self.temperature = temperature
        self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=temperature)

        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", self._get_system_prompt()),
                ("human", self._get_generation_prompt()),
            ]
        )

        self.parser = JsonOutputParser()
        self.chain = self.prompt_template | self.llm | self.parser

    def _get_system_prompt(self) -> str:
        return """
        <system_prompt>
        <role>
            <primary_function>experienced Excel interviewer</primary_function>
            <interview_style>conversational interview</interview_style>
            <communication_tone>calm, measured, and naturally professional</communication_tone>
        </role>

        <critical_output_requirements>
            <format_restriction>ONLY valid JSON - no additional text before or after</format_restriction>
            <json_structure_mandatory>EXACT format compliance required</json_structure_mandatory>
            <forbidden_elements>
            <element>markdown formatting</element>
            <element>explanatory text outside JSON</element>
            <element>additional commentary</element>
            </forbidden_elements>
        </critical_output_requirements>

        <json_schema>
            <required_format>
            {{
                "text": "Your complete conversational response (acknowledgment + next question/comment)",
                "phase_transition": false,
                "new_phase": null,
                "coverage_assessment": "Brief note on what domains you've covered and what's still needed",
                "reasoning": "Why you're asking this question or making this transition"
            }}
            </required_format>
            
            <field_specifications>
            <text>
                <content>complete conversational response</content>
                <components>acknowledgment + next question/comment</components>
            </text>
            <phase_transition>
                <data_type>boolean</data_type>
                <purpose>indicates if moving to new interview phase</purpose>
            </phase_transition>
            <new_phase>
                <data_type>string or null</data_type>
                <purpose>name of new phase if transitioning</purpose>
            </new_phase>
            <coverage_assessment>
                <content>brief note on domains covered and what's still needed</content>
                <format>concise summary</format>
            </coverage_assessment>
            <reasoning>
                <content>explanation for current question or transition</content>
                <purpose>justify interviewer's strategic choice</purpose>
            </reasoning>
            </field_specifications>
        </json_schema>

        <interview_behavior>
            <conversational_approach>
            <style>natural conversation flow</style>
            <professionalism>maintain professional standards</professionalism>
            <continuity>reference previous answers when relevant</continuity>
            <engagement>show measured interest in candidate's Excel expertise</engagement>
            <demeanor>composed, thoughtful, human-like questioning style</demeanor>
            </conversational_approach>
        </interview_behavior>

        <adaptive_strategies>
            <response_patterns>
            <strong_answers>
                <action>ask deeper/more complex questions</action>
                <escalation>increase difficulty level</escalation>
            </strong_answers>
            <weak_answers>
                <action>simplify or try different angle</action>
                <support>provide alternative approaches</support>
            </weak_answers>
            <partial_knowledge>
                <action>probe to understand actual level</action>
                <assessment>determine true competency boundaries</assessment>
            </partial_knowledge>
            </response_patterns>
            
            <difficulty_adaptation>
            <method>adapt based on candidate responses</method>
            <goal>match questions to demonstrated skill level</goal>
            </difficulty_adaptation>
        </adaptive_strategies>

        <example_response>
            <valid_json_sample>
            {{
                "text": "I see. Can you tell me about your experience with PivotTables? How would you approach creating one?", 
                "phase_transition": false, 
                "new_phase": null, 
                "coverage_assessment": "Covered formulas, now exploring PivotTables", 
                "reasoning": "Moving to next core Excel domain"
            }}
            </valid_json_sample>
        </example_response>

        <final_reminder>
            <output_constraint>Return ONLY the JSON object, nothing else</output_constraint>
            <format_validation>Ensure valid JSON syntax</format_validation>
            <content_completeness>Include all required fields in response</content_completeness>
        </final_reminder>
        </system_prompt>
        """

    def _get_generation_prompt(self) -> str:
        return """
        <system_prompt>
        <interview_context>
            <current_state>
            <phase>{phase}</phase>
            <questions_asked>{questions_count}</questions_asked>
            <target_questions>{target_questions}</target_questions>
            </current_state>
            
            <conversation_history>
            {chat_history}
            </conversation_history>
            
            <candidate_analysis>
            {performance_summary}
            </candidate_analysis>
            
            <timing_status>
            {time_status}
            </timing_status>
        </interview_context>

        <interviewer_role>
            <position>experienced Excel interviewer</position>
            <authority>full control over interview flow</authority>
            <primary_goal>assess candidate across core Excel domains</primary_goal>
        </interviewer_role>

        <coverage_requirements>
            <required_domains>
            <domain id="1" name="data_entry_cleanup">
                <focus>data validation, formatting, cleaning techniques</focus>
            </domain>
            <domain id="2" name="formulas_functions">
                <focus>VLOOKUP, INDEX/MATCH, complex formulas</focus>
            </domain>
            <domain id="3" name="pivot_tables">
                <focus>creating, customizing, analyzing data</focus>
            </domain>
            <domain id="4" name="scenario_analysis">
                <focus>Goal Seek, data tables, scenario manager</focus>
            </domain>
            <domain id="5" name="reflection_meta">
                <focus>learning approach, problem-solving process</focus>
            </domain>
            </required_domains>
        </coverage_requirements>

        <interview_flow_control>
            <flow_decisions>
            <topic_switching>
                <trigger>satisfaction with current domain knowledge</trigger>
                <action>move to another uncovered domain</action>
            </topic_switching>
            
            <follow_up_depth>
                <criteria>determine sufficient evidence threshold</criteria>
                <control>decide follow-up quantity needed</control>
            </follow_up_depth>
            
            <phase_transitions>
                <qa_to_reflection>
                <condition>adequate domain coverage achieved</condition>
                <action>phase_transition: true, new_phase: "reflection"</action>
                </qa_to_reflection>
                <reflection_to_closing>
                <condition>reflection phase completed</condition>
                <action>phase_transition: true, new_phase: "closing"</action>
                </reflection_to_closing>
            </phase_transitions>
            
            <pacing_control>
                <adaptation>adjust questioning speed based on responses and time</adaptation>
                <balance>optimize depth vs breadth given constraints</balance>
            </pacing_control>
            </flow_decisions>
        </interview_flow_control>

        <decision_framework>
            <continue_current_area>
            <condition>need more evidence in current domain</condition>
            <json_response>phase_transition: false</json_response>
            <action>continue with follow-ups</action>
            </continue_current_area>
            
            <switch_domains>
            <condition>satisfied with current area</condition>
            <json_response>phase_transition: false, new question</json_response>
            <action>switch to uncovered domain</action>
            </switch_domains>
            
            <move_to_reflection>
            <condition>covered enough domains</condition>
            <json_response>phase_transition: true, new_phase: "reflection"</json_response>
            </move_to_reflection>
            
            <close_interview>
            <condition>reflection phase completed</condition>
            <json_response>phase_transition: true, new_phase: "closing"</json_response>
            </close_interview>
        </decision_framework>

        <time_management>
            <efficiency_principle>use remaining time strategically for core coverage</efficiency_principle>
            
            <time_thresholds>
            <critical_point>
                <time_marker>12+ minutes elapsed</time_marker>
                <strategy>prioritize uncovered areas</strategy>
            </critical_point>
            </time_thresholds>
            
            <pacing_philosophy>
            <approach>strategic about depth vs breadth</approach>
            <constraint>don't rush but be efficient</constraint>
            </pacing_philosophy>
        </time_management>

        <output_requirement>
            <format>specified JSON format</format>
            <instruction>return the question in required JSON structure</instruction>
        </output_requirement>
        </system_prompt>
        """

    def generate_next_response(
        self, state: InterviewState, time_status: dict = None
    ) -> dict:
        try:
            chat_history = self._format_chat_history(state)
            performance_summary = self._analyze_performance(state)

            if time_status is None:
                current_time = datetime.now(tz=timezone.utc)
                elapsed = current_time - state.start_time
                elapsed_minutes = elapsed.total_seconds() / 60.0
                time_status = {
                    "elapsed_minutes": elapsed_minutes,
                    "remaining_minutes": max(0, 15 - elapsed_minutes),
                    "time_up": elapsed_minutes >= 15,
                    "time_warning": elapsed_minutes >= 12,
                }

            try:
                formatted_time_status = self._format_time_status(time_status)
            except Exception as e:
                logger.error(f"Error formatting time status: {e}")
                formatted_time_status = "Time status unavailable"

            template_vars = {
                "phase": str(state.phase or "qa"),
                "questions_count": len(state.responses or []),
                "target_questions": "No fixed target - you decide when enough coverage is achieved",
                "chat_history": str(
                    chat_history
                    or "No previous responses yet - this is the first question."
                ),
                "performance_summary": str(
                    performance_summary or "Starting interview assessment"
                ),
                "time_status": formatted_time_status,
            }

            logger.debug(f"Template variables: {template_vars}")

            try:
                result = self.chain.invoke(template_vars)
            except Exception as parse_error:
                logger.error(f"JSON parsing failed: {parse_error}")
                try:
                    raw_chain = self.prompt_template | self.llm
                    raw_result = raw_chain.invoke(template_vars)
                    logger.error(
                        f"Raw LLM response that failed to parse: {raw_result.content}"
                    )
                    result = self._validate_and_fix_json_response(raw_result.content)
                except Exception as e:
                    logger.error(f"Could not get or fix raw response: {e}")
                    result = {
                        "text": "Let me start by asking about your Excel experience. How comfortable are you with creating formulas and functions?",
                        "phase_transition": False,
                        "new_phase": None,
                        "coverage_assessment": "Starting with formulas assessment",
                        "reasoning": "Fallback due to JSON parsing error",
                    }

            if not result.get("phase_transition", False):
                question_id = f"q{len(state.responses) + 1}"
                question = Question(
                    id=question_id,
                    text=result.get("text", "Tell me about your Excel experience."),
                    type="qa",
                    metadata={
                        "coverage_assessment": result.get("coverage_assessment", ""),
                        "reasoning": result.get("reasoning", "Generated dynamically"),
                        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
                    },
                )
                state.questions.append(question)

            return {
                "text": result.get("text", "Let me ask about your Excel experience."),
                "phase_transition": result.get("phase_transition", False),
                "new_phase": result.get("new_phase"),
                "coverage_assessment": result.get("coverage_assessment", ""),
                "reasoning": result.get("reasoning", ""),
            }

        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return {
                "text": "Let me ask you about your Excel experience. How comfortable are you with creating and working with formulas?",
                "phase_transition": False,
                "new_phase": None,
                "coverage_assessment": "Starting with formulas assessment",
                "reasoning": "Fallback question due to generation error",
            }

    def _format_chat_history(self, state: InterviewState) -> str:
        if not state.responses:
            return "No previous responses yet - this is the first question."

        history_parts = []
        for i, response in enumerate(state.responses, 1):
            history_parts.append(f"Q{i}: {response.question_text}")
            history_parts.append(f"A{i}: {response.answer_text}")
            if response.scores and response.rationale:
                overall_score = response.scores.get("overall", 0)
                history_parts.append(
                    f"Score: {overall_score:.1f}/5.0 - {response.rationale}"
                )
            history_parts.append("")

        return "\n".join(history_parts)

    def _analyze_performance(self, state: InterviewState) -> str:
        if not state.responses:
            return "First question - no performance data yet. Start with a foundational technical question to gauge their level."

        total_responses = len(state.responses)
        latest_response = state.responses[-1] if state.responses else None

        avg_scores = {}
        score_dimensions = [
            "correctness",
            "design",
            "communication",
            "production",
            "overall",
        ]

        for dim in score_dimensions:
            scores = [r.scores.get(dim, 0) for r in state.responses if r.scores]
            avg_scores[dim] = sum(scores) / len(scores) if scores else 0

        strengths = []
        weaknesses = []
        moderate_areas = []

        for dim, avg_score in avg_scores.items():
            if avg_score >= 4.0:
                strengths.append(dim)
            elif avg_score <= 2.5:
                weaknesses.append(dim)
            else:
                moderate_areas.append(dim)

        categories_covered = set()
        difficulty_trend = []

        for i, response in enumerate(state.responses):
            if hasattr(response, "question_text"):
                for question in state.questions:
                    if question.text == response.question_text and question.metadata:
                        categories_covered.add(
                            question.metadata.get("category", "general")
                        )
                        difficulty_trend.append(
                            question.metadata.get("difficulty", "intermediate")
                        )

        last_question_difficulty = (
            difficulty_trend[-1] if difficulty_trend else "intermediate"
        )
        last_score = (
            latest_response.scores.get("overall", 0)
            if latest_response and latest_response.scores
            else 0
        )

        performance_trend = "stable"
        if len(state.responses) >= 2:
            recent_scores = [
                r.scores.get("overall", 0) for r in state.responses[-2:] if r.scores
            ]
            if len(recent_scores) == 2:
                if recent_scores[1] > recent_scores[0] + 0.5:
                    performance_trend = "improving"
                elif recent_scores[1] < recent_scores[0] - 0.5:
                    performance_trend = "declining"

        adaptive_guidance = ""
        if last_score >= 4.0:
            adaptive_guidance = "INCREASE DIFFICULTY - Last answer was strong, push harder with optimization/edge cases"
        elif last_score <= 1.5:
            adaptive_guidance = "INADEQUATE RESPONSE - Last answer was insufficient (likely 'no', 'yes', or minimal). STAY ON SAME TOPIC and ask follow-up questions to get them to elaborate. Don't move to new topics."
        elif last_score <= 2.5:
            adaptive_guidance = "DECREASE DIFFICULTY - Last answer struggled, simplify or pivot to their strengths"
        else:
            adaptive_guidance = "PROBE DEEPER - Last answer was partial, explore their understanding further"

        summary_parts = [
            f"Responses: {total_responses}",
            f"Overall avg: {avg_scores['overall']:.1f}/5.0",
            f"Last score: {last_score:.1f}/5.0 ({last_question_difficulty})",
            f"Trend: {performance_trend}",
            adaptive_guidance,
        ]

        if strengths:
            summary_parts.append(f"Strengths: {', '.join(strengths)}")
        if weaknesses:
            summary_parts.append(f"Weaknesses: {', '.join(weaknesses)}")
        if categories_covered:
            summary_parts.append(f"Topics covered: {', '.join(categories_covered)}")

        if latest_response and latest_response.rationale:
            summary_parts.append(f"Last feedback: {latest_response.rationale[:100]}...")

        return " | ".join(summary_parts)

    def _format_time_status(self, time_status: dict) -> str:
        """Format timing information for the prompt"""
        if not time_status:
            return "Time status unavailable"

        elapsed = time_status.get("elapsed_minutes", 0)
        remaining = time_status.get("remaining_minutes", 15)

        status_parts = [
            f"Elapsed: {elapsed:.1f} minutes",
            f"Remaining: {remaining:.1f} minutes",
        ]

        if time_status.get("time_up", False):
            status_parts.append("TIME UP - Should move to reflection")
        elif time_status.get("time_warning", False):
            status_parts.append("TIME WARNING - Interview should wrap up soon")
        else:
            status_parts.append("Time available for more questions")

        return " | ".join(status_parts)

    def _validate_and_fix_json_response(self, raw_response: str) -> dict:
        """Validate and attempt to fix JSON responses from the LLM"""
        try:
            import json

            return json.loads(raw_response)
        except json.JSONDecodeError:
            import re

            json_match = re.search(
                r"```json\s*(\{.*?\})\s*```", raw_response, re.DOTALL
            )
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

            json_match = re.search(r"(\{.*?\})", raw_response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

            logger.warning(f"Could not parse JSON response: {raw_response}")
            return {
                "text": "Let me ask about your Excel experience. What's your comfort level with formulas and functions?",
                "phase_transition": False,
                "new_phase": None,
                "coverage_assessment": "Starting Excel assessment",
                "reasoning": "Fallback due to unparseable response",
            }

    def _create_fallback_question(self, state: InterviewState) -> Question:
        fallback_questions = [
            "How do you approach debugging a complex technical issue?",
            "Describe a challenging technical project you've worked on recently.",
            "What's your experience with database optimization?",
            "How do you ensure code quality in your development process?",
            "Tell me about your experience with distributed systems.",
        ]

        question_index = len(state.responses) % len(fallback_questions)
        question_text = fallback_questions[question_index]

        return Question(
            id=f"fallback_q{len(state.responses) + 1}",
            text=question_text,
            type="qa",
            metadata={
                "category": "general",
                "difficulty": "intermediate",
                "reasoning": "Fallback question due to generation error",
                "generated_at": datetime.now(tz=timezone.utc).isoformat(),
            },
        )

    def generate_scenario_question(self, state: InterviewState) -> str:
        try:
            scenario_prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """<interviewer_role>
              <function>conversational technical interviewer</function>
              <task>create practical scenario question</task>
              <personality>
                <trait>naturally engaging</trait>
                <trait>genuinely curious</trait>
                <trait>interested in problem-solving approach</trait>
              </personality>
            </interviewer_role>

            <scenario_requirements>
              <conversation_flow>
                <acknowledgment>natural acknowledgment of previous responses</acknowledgment>
                <continuity>feels like natural conversation continuation</continuity>
                <connection>references or builds upon discussed topics</connection>
              </conversation_flow>
              
              <assessment_goals>
                <focus>practical problem-solving ability</focus>
                <thinking>system thinking evaluation</thinking>
                <presentation>conversational and engaging delivery</presentation>
              </assessment_goals>
              
              <transition_examples>
                <example>"That's been really helpful! Now I'd like to shift to..."</example>
                <example>"Great insights so far. Let's try a different kind of question..."</example>
                <example>"I'm getting a good sense of your background. Now I'm curious how you'd approach..."</example>
              </transition_examples>
            </scenario_requirements>

            <output_specification>
              <format>complete conversational response</format>
              <components>acknowledgment + scenario question</components>
              <tone>natural, measured professional interest</tone>
            </output_specification>""",
                    ),
                    (
                        "human",
                        """<conversation_context>
              <label>Based on our conversation so far:</label>
              <content>{chat_history}</content>
            </conversation_context>

            <candidate_assessment>
              <label>Candidate insights:</label>
              <content>{performance_summary}</content>
            </candidate_assessment>

            <scenario_objectives>
              <transition_goal>shift to practical scenario</transition_goal>
              
              <scenario_criteria>
                <criterion id="1">builds on topics discussed or demonstrated expertise</criterion>
                <criterion id="2">tests real-world problem-solving approach</criterion>
                <criterion id="3">matches their technical level and interests</criterion>
                <criterion id="4">feels like natural next step in conversation</criterion>
              </scenario_criteria>
            </scenario_objectives>

            <creation_instructions>
              <task>create conversational scenario question</task>
              <requirements>
                <reference_previous>reference our previous discussion</reference_previous>
                <present_challenge>present engaging real-world challenge</present_challenge>
                <maintain_tone>use measured, curious tone showing genuine interest</maintain_tone>
              </requirements>
            </creation_instructions>""",
                    ),
                ]
            )
            scenario_chain = scenario_prompt | self.llm

            chat_history = self._format_chat_history(state)
            performance_summary = self._analyze_performance(state)

            result = scenario_chain.invoke(
                {
                    "chat_history": chat_history,
                    "performance_summary": performance_summary,
                }
            )

            return result.content

        except Exception as e:
            logger.error(f"Failed to generate scenario question: {e}")
            return """Thanks for sharing your insights so far - I'm getting a good sense of your technical background! Now I'd love to shift gears and explore your problem-solving approach with a practical scenario.

Imagine you're working on a web application that has become very slow - users are complaining about page load times exceeding 10 seconds. This is the kind of challenge that can really test your systematic thinking.

I'm curious: how would you approach diagnosing and fixing this performance issue? Walk me through your thought process - what tools would you reach for first, what would you investigate, and what are some of the common culprits you'd consider?"""

    def generate_reflection_question(
        self, state: InterviewState, time_status: dict = None
    ) -> str:
        try:
            reflection_prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """<interviewer_role>
              <function>thoughtful technical interviewer</function>
              <phase>wrapping up conversational interview</phase>
              <personality>
                <trait>supportive and encouraging</trait>
                <trait>genuinely interested in candidate's growth journey</trait>
                <trait>mentoring approach</trait>
              </personality>
            </interviewer_role>

            <reflection_requirements>
              <conversation_flow>
                <acknowledgment>natural acknowledgment of scenario response and overall conversation</acknowledgment>
                <conclusion>feels like natural, supportive conclusion</conclusion>
                <connection>references specific topics or insights from discussion</connection>
              </conversation_flow>
              
              <development_focus>
                <learning>encourage thinking about learning journey</learning>
                <growth>show genuine interest in professional development</growth>
                <mentorship>supportive mentor tone</mentorship>
              </development_focus>
              
              <transition_examples>
                <example>"That was excellent problem-solving! As we wrap up..."</example>
                <example>"I really appreciate how you worked through that. To close out our conversation..."</example>
                <example>"Thanks for sharing your approach to that challenge. Before we finish..."</example>
              </transition_examples>
            </reflection_requirements>

            <time_awareness>
              <fifteen_minute_limit>
                <acknowledgment>acknowledge naturally if time limit reached</acknowledgment>
                <example>"I notice we've reached our time limit, so let's wrap up with a quick reflection..."</example>
                <example>"Time flies when you're having a good technical discussion! Let's close with..."</example>
              </fifteen_minute_limit>
            </time_awareness>

            <output_specification>
              <format>complete conversational response</format>
              <components>acknowledgment + reflection question</components>
              <tone>warm, encouraging, supportive mentor</tone>
            </output_specification>""",
                    ),
                    (
                        "human",
                        """<conversation_context>
              <label>Based on our wonderful conversation:</label>
              <content>{chat_history}</content>
            </conversation_context>

            <timing_context>
              <label>Interview timing:</label>
              <content>{time_status}</content>
            </timing_context>

            <reflection_objectives>
              <wrap_up_goal>end on reflective note</wrap_up_goal>
              
              <development_areas>
                <area id="1">their learning and development journey</area>
                <area id="2">areas they're excited to grow in (perhaps inspired by our discussion)</area>
                <area id="3">their technical interests and where they want to head next</area>
              </development_areas>
            </reflection_objectives>

            <creation_instructions>
              <task>create warm, encouraging reflection question</task>
              <requirements>
                <reference_conversation>reference our conversation</reference_conversation>
                <show_interest>show genuine interest in their growth</show_interest>
                <mentoring_tone>feel like supportive mentor asking about development goals</mentoring_tone>
              </requirements>
            </creation_instructions>""",
                    ),
                ]
            )

            reflection_chain = reflection_prompt | self.llm

            chat_history = self._format_chat_history(state)

            if time_status is None:
                from datetime import datetime, timezone

                current_time = datetime.now(tz=timezone.utc)
                elapsed = current_time - state.start_time
                elapsed_minutes = elapsed.total_seconds() / 60.0
                time_status = {
                    "elapsed_minutes": elapsed_minutes,
                    "remaining_minutes": max(0, 15 - elapsed_minutes),
                    "time_up": elapsed_minutes >= 15,
                    "time_warning": elapsed_minutes >= 12,
                }

            result = reflection_chain.invoke(
                {
                    "chat_history": chat_history,
                    "time_status": self._format_time_status(time_status),
                }
            )

            return result.content

        except Exception as e:
            logger.error(f"Failed to generate reflection question: {e}")
            return """That was really insightful - I appreciate how you worked through that challenge! As we wrap up our conversation, I'm really curious about your learning journey. 

Looking back at our discussion today - and thinking about your technical interests and goals - what's one area you're excited to dive deeper into or improve? It could be something we touched on today, or perhaps something you've been thinking about lately.

I'd love to hear not just what you want to learn, but also how you're thinking about approaching that growth. What's your plan or strategy for developing in that area?"""

    def generate_reflection_response(
        self, state: InterviewState, time_status: dict = None
    ) -> dict:
        """Generate reflection response with agent control over when to close the interview"""
        try:
            from datetime import datetime, timezone

            reflection_prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """<interviewer_role>
              <function>thoughtful technical interviewer</function>
              <phase>wrapping up conversational interview</phase>
              <personality>
                <trait>supportive and encouraging</trait>
                <trait>genuinely interested in candidate's growth journey</trait>
                <trait>mentoring approach</trait>
              </personality>
            </interviewer_role>

            <reflection_requirements>
              <conversation_flow>
                <acknowledgment>natural acknowledgment of scenario response and overall conversation</acknowledgment>
                <conclusion>feels like natural, supportive conclusion</conclusion>
                <connection>references specific topics or insights from discussion</connection>
              </conversation_flow>
              
              <development_focus>
                <learning>encourage thinking about learning journey</learning>
                <growth>show genuine interest in professional development</growth>
                <mentorship>supportive mentor tone</mentorship>
              </development_focus>
              
              <transition_examples>
                <example>"That was excellent problem-solving! As we wrap up..."</example>
                <example>"I really appreciate how you worked through that. To close out our conversation..."</example>
                <example>"Thanks for sharing your approach to that challenge. Before we finish..."</example>
              </transition_examples>
            </reflection_requirements>

            <time_awareness>
              <fifteen_minute_limit>
                <acknowledgment>acknowledge naturally if time limit reached</acknowledgment>
                <example>"I notice we've reached our time limit, so let's wrap up with a quick reflection..."</example>
                <example>"Time flies when you're having a good technical discussion! Let's close with..."</example>
              </fifteen_minute_limit>
            </time_awareness>

            <output_specification>
              <format>complete conversational response</format>
              <components>acknowledgment + reflection question</components>
              <tone>warm, encouraging, supportive mentor</tone>
            </output_specification>""",
                    ),
                    (
                        "human",
                        """<conversation_context>
              <label>Based on our wonderful conversation:</label>
              <content>{chat_history}</content>
            </conversation_context>

            <timing_context>
              <label>Interview timing:</label>
              <content>{time_status}</content>
            </timing_context>

            <reflection_objectives>
              <wrap_up_goal>end on reflective note</wrap_up_goal>
              
              <development_areas>
                <area id="1">their learning and development journey</area>
                <area id="2">areas they're excited to grow in (perhaps inspired by our discussion)</area>
                <area id="3">their technical interests and where they want to head next</area>
              </development_areas>
            </reflection_objectives>

            <creation_instructions>
              <task>create warm, encouraging reflection question</task>
              <requirements>
                <reference_conversation>reference our conversation</reference_conversation>
                <show_interest>show genuine interest in their growth</show_interest>
                <mentoring_tone>feel like supportive mentor asking about development goals</mentoring_tone>
              </requirements>
            </creation_instructions>""",
                    ),
                ]
            )
            reflection_chain = reflection_prompt | self.llm | self.parser

            chat_history = self._format_chat_history(state)

            if time_status is None:
                current_time = datetime.now(tz=timezone.utc)
                elapsed = current_time - state.start_time
                elapsed_minutes = elapsed.total_seconds() / 60.0
                time_status = {
                    "elapsed_minutes": elapsed_minutes,
                    "remaining_minutes": max(0, 15 - elapsed_minutes),
                    "time_up": elapsed_minutes >= 15,
                    "time_warning": elapsed_minutes >= 12,
                }

            result = reflection_chain.invoke(
                {
                    "chat_history": chat_history,
                    "time_status": self._format_time_status(time_status),
                }
            )

            return {
                "text": result.get("text", "Thank you for that reflection."),
                "phase_transition": result.get("phase_transition", False),
                "new_phase": result.get("new_phase"),
                "assessment_complete": result.get("assessment_complete", ""),
            }

        except Exception as e:
            logger.error(f"Failed to generate reflection response: {e}")
            return {
                "text": "Thank you for sharing your thoughts on learning and growth. That gives me great insight into your approach to professional development.",
                "phase_transition": True,
                "new_phase": "closing",
                "assessment_complete": "Sufficient information gathered",
            }
