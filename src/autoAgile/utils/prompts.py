import os
import re as _re
import unicodedata
import json
from docx import Document
# Updated imports for modern LangChain (all moved to langchain_core)
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
# Note: ChatOpenAI import kept for backward compatibility, but llm_factory should be used
try:
    from langchain_openai import ChatOpenAI, OpenAI
except ImportError:
    pass

#set env variable auth_key to be the key
output_parser = StrOutputParser()
threshold = 5

def _json_chain(prompt, chat, op):
    """Enforce JSON-only output for Ollama; other providers use the plain chain."""
    if type(chat).__name__ == 'ChatOllama':
        return prompt | chat.bind(format="json") | op
    return prompt | chat | op

def _strip_fences(text: str) -> str:
    """
    Remove markdown code fences and extract the outermost JSON block from prose.

    Local LLMs frequently wrap JSON in explanatory text, e.g.:
        "Here are the user stories:\n```json\n{...}\n```\nLet me know..."
    A simple .replace("```","") strips fences but leaves the prose, which
    breaks json.loads(). This function uses depth-tracked brace matching so
    the returned string is always the raw JSON object/array — never mixed prose.
    """
    # 1. Strip code-fence marker lines (```json or ```)
    text = _re.sub(r'^```(?:json)?\s*$', '', text, flags=_re.MULTILINE).strip()

    # 2. If the whole string is already valid JSON, return it as-is
    try:
        json.loads(text)
        return text
    except (json.JSONDecodeError, ValueError):
        pass

    # 3. Use depth-tracked search to find the outermost { ... } or [ ... ]
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        start_idx = text.find(start_char)
        if start_idx == -1:
            continue
        depth = 0
        in_string = False
        escape_next = False
        for i, ch in enumerate(text[start_idx:], start=start_idx):
            if escape_next:
                escape_next = False
                continue
            if ch == '\\' and in_string:
                escape_next = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == start_char:
                depth += 1
            elif ch == end_char:
                depth -= 1
                if depth == 0:
                    candidate = text[start_idx:i + 1]
                    try:
                        json.loads(candidate)
                        return candidate
                    except (json.JSONDecodeError, ValueError):
                        break  # malformed — try [ ... ] next

    # 4. Nothing parseable found; return whatever we have
    return text

def extract_text_from_docx(docx_path):
    doc = Document(docx_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def clean_doc(doc_text:str, chat)->str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an assistant that help improve the input document. You will correct grammar mistakes,
         remove meaningless words or characters from the input document and improve its formatting."""),
        ("user", "{input}")
    ])
    chain = prompt | chat | output_parser
    re = chain.invoke({"input": doc_text})
    return re

def summarize_doc(doc_text:str, chat)->str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a software project manager. Please extract the text that describes the application we need
         to build the input document. Your summary should focused on the functional requirements."""),
        ("user", "{input}")
    ])
    chain = prompt | chat | output_parser
    re = chain.invoke({"input": doc_text})
    return re

def refine_doc(doc_text: str, chat, mode)->str:
    cleaned = clean_doc(doc_text, chat)
    #re = summarize_doc(cleaned, chat)
    return cleaned

def extract_list(doc_text:str,chat)->str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a senior software engineer extracting ALL functional requirements from a product specification document.

Rules:
1. Extract EVERY distinct functional requirement mentioned — do not skip, merge, or summarise.
2. Each requirement must be one sentence starting with "The system must ..." using a precise verb (collect, calculate, transmit, validate, store, monitor, display, alert, authenticate, encrypt).
3. Cover ALL functional areas: data acquisition, processing/calculation, storage, transmission, user interface, error handling, safety/security, configuration, alerts/notifications, reporting.
4. Do NOT include meta-requirements about testing, documentation, or project management.
5. If a sentence describes two distinct capabilities, split it into two requirements.
6. Aim for completeness — it is better to have too many specific requirements than too few.

Output format: one requirement per line, no numbering, no headings."""),
        ("user", "{input}")
    ])
    chain = prompt | chat | output_parser
    re = chain.invoke({"input": doc_text})
    return re

def compare_answer(answer_left, answer_right,chat)->bool:
    prompt = (PromptTemplate.from_template("""Please compare the two input software requirement lists and determine whether
                                           they are describing the same list of requirements. Given the first list:\n
                                        {input_first}\n and the second:\n" {input_second}\n", are they describing the
                                           same requirements? Please provide reasoning steps in your answer, also with
                                           keyword yes indicating they are the same or no indicating they are not the
                                           same."""))

    # Use LangChain's LCEL (modern syntax)
    chain = prompt | chat | output_parser
    re_text = chain.invoke({"input_first":answer_left, "input_second":answer_right})
    
    print("=============================\n")
    print(re_text) 
    print("=============================\n")
    return ("yes" in re_text.lower())


def self_consistency(answers: list[str], chat)->str:
    votes = {answers[0]: 1} 
    find = False
    for answer in answers[1:]:
        for k in votes.keys():
            if compare_answer(k, answer, chat):
                votes[k] +=1
                find = True
                break
        if not find:
            votes[answer] = 1
            find = False
    print(votes)
    result = max(votes, key=votes.get)
    print(result)
    return result

def rank_answer(answer_left, answer_right,chat, mode="debug")->str:
    prompt = (PromptTemplate.from_template("""As a software developer, you vote for the software requirement list that is more detailed and specific.\n
                                           \nGiven two input texts, the first:\n
                                        {input_first}\n and the second:\n" {input_second}\n", which one you vote for?
                                           Please only answer with your vote."""))

    # Use LangChain's LCEL (modern syntax)
    chain = prompt | chat | output_parser
    re_text = chain.invoke({"input_first":answer_left, "input_second":answer_right})
    
    better = None
    if '1' in re_text.lower() or 'first' in re_text.lower():
        better = answer_left
    elif '2' in re_text.lower() or "second" in re_text.lower():
        better = answer_right
    else:
        # Default to first answer if unclear
        better = answer_left
        
    if mode == "debug":
        print("=============================\n")
        print(re_text)
        print("===========the better result is=========\n")
        print(better)
        print("=============================\n")
    return better

def c_o_t(answers: list[str], chat, mode="debug")->str:
    better = answers[0]
    for answer in answers[1:]:
        better = rank_answer(better, answer, chat, mode)
    return better


def extract_functionarity(doc_text:str,chat, mode="debug")->str:
    requirements = [extract_list(doc_text, chat) for i in range(threshold)]
    return c_o_t(requirements, chat, mode)

def refine_requirements(requirements:str,chat,mode)->str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a senior software project manager refining a list of functional requirements before user story generation.

Apply these rules in order:
1. SPLIT: If any single requirement bundles two or more distinct capabilities, split it into separate requirements. Err on the side of splitting.
2. CLARIFY: Rewrite vague verbs ("handle", "support", "manage", "provide") to precise ones ("store", "validate", "transmit", "calculate", "alert", "display", "authenticate").
3. ADD: Insert clearly implied requirements that are missing (e.g., if data is transmitted it must first be aggregated; if a user logs in there must be a way to log out).
4. REMOVE: Delete ONLY exact duplicate requirements. Do NOT merge requirements that cover different functional areas — keep them separate.
5. PRESERVE: Keep the total number of requirements high. It is better to have 15 specific requirements than 5 merged ones.

Output ONLY the refined list, one requirement per line, each starting with "The system must ...".
Do NOT include explanations, headings, or numbering."""),
        ("user", "{input}")
    ])
    chain = prompt | chat | output_parser
    re = chain.invoke({"input": requirements})
    return re

def extract_epics(requirements:str,chat, mode)->str:
    pp = """given the input software requirements,please give us the deliverables that we can assign to our
         developers. Each requirement should has its own description. For each functional requirement, the deliverables should be selected from architecture design, database
         schema design, unit tests, user training documentation and production support plan based on your judgement.
         Your response should be in Json format. This this an example output:
         '{{
            "Epics": [
                {{
                    "User Story": "The system must perform local data processing and aggregation before transmitting data via satellite.",
                    "Deliverables": {{
                        "architecture_design": "Design of the data processing and aggregation modules within the system."
                    }}
                }}
            ]
          }}'.
        """
    prompt = ChatPromptTemplate.from_messages([
        ("system", pp),
        ("user", "{input}")
    ])
    chain = _json_chain(prompt, chat, output_parser)
    re = chain.invoke({"input": requirements})
    return _strip_fences(re)

def extract_epics_v2(requirements:str,chat, mode)->str:
    """Enhanced v2: Creates detailed user stories with specific elements clause and proper decomposition"""
    pp = """RESPOND WITH JSON ONLY. Do not include any prose, explanations, markdown headers, or text outside the JSON. Your entire response must be a single valid JSON object starting with { and ending with }.

You are an automated requirements-to-user-story engine. Generate detailed, engineering-ready user stories.

USER STORY FORMAT (MANDATORY):
The <system/actor> must <specific capability> using [specific elements: <concrete items, fields, instruments, parameters, or thresholds taken verbatim from the requirements>], so that <concrete business or engineering outcome>.

RULES FOR EACH CLAUSE:
- "must <specific capability>" — use a precise verb (collect, calculate, transmit, validate, store, monitor). Never use vague verbs like "handle", "manage", "support", "provide".
- "[specific elements: ...]" — MANDATORY. List the ACTUAL named components, fields, sensors, or parameters from the requirement. "sensors" alone is NOT acceptable; name them (e.g., anemometer, thermometer).
- "so that <outcome>" — state a concrete, testable outcome. NOT "data is available" — instead say who benefits and what they can do (e.g., "so that the Fleet Operations Center can detect instrument failures within 30 seconds").

WHEN TO SPLIT A REQUIREMENT INTO MULTIPLE STORIES (SPLIT TRIGGERS):
Split a requirement into separate user stories whenever it contains:
(a) Multiple actors or subsystems involved
(b) Multiple distinct capabilities or workflows
(c) Separable concerns: data acquisition vs. processing/aggregation vs. storage vs. transmission
(d) Happy path PLUS failure/recovery/fault-reporting/degraded-mode behavior
(e) Configuration, monitoring, or administrative variants of the same feature
(f) A distinct non-functional requirement (security, performance, power, reliability) attached to a functional feature
(g) Lifecycle operations: install, update/upgrade, reconfigure, backup/failover, decommission

Example: "The system must collect sensor data, process it, and transmit to server when connection is available"
→ Split into 3 stories: (1) Collect sensor data, (2) Process sensor data, (3) Transmit data to server

DO NOT CREATE META-STORIES:
- Do NOT create stories about "Integration Testing", "Documentation", "Testing Coverage"
- These are HOW you validate, not WHAT you build
- Create ONLY functional and non-functional requirement stories

TITLE FIELD (MANDATORY):
Each story must include a "Title" field: 3-5 words, Title Case, describing the core action.
- ✅ GOOD: "Collect Sensor Readings Periodically", "Transmit Compressed Data Packets", "Validate Patient Demographics"
- ❌ BAD: "Collect Data From A Set" (truncated), "System Must Handle Data" (vague), "User Story 1" (generic)

DELIVERABLE OPTIONS (select 2-4 per user story):
- architecture_design: Design of specific modules, components, algorithms, system architecture
- database_schema_design: Database schema with specific tables, fields, relationships
- api_endpoints: API/interface contracts for integration points
- unit_tests: Tests to verify specific functionality
- integration_tests: Tests for component interactions
- error_handling: Fault detection, reporting, and recovery mechanisms
- security_controls: Authentication, authorization, encryption, validation
- performance_optimization: Caching, indexing, query optimization
- monitoring_logging: Telemetry, metrics, alerts, observability
- user_documentation: End-user guides and training materials

OUTPUT FORMAT:
{{
    "Epics": [
        {{
            "Title": "3-5 Word Action Title",
            "User Story": "The <system> must <specific capability> using [specific elements: <field1, field2, sensor3, parameter4>], so that <concrete, testable outcome>.",
            "Deliverables": {{
                "architecture_design": "Design of the <specific module names> including <specific components: algorithms, interfaces, workflows> to enable <specific functionality>.",
                "database_schema_design": "Schema with tables <table1, table2> containing fields [field1, field2, field3] to support <specific operations>.",
                "unit_tests": "Tests to verify <specific component> correctly <specific behavior> with <specific scenarios>."
            }}
        }}
    ]
}}

CRITICAL RULES:
1. "Title" field is MANDATORY — 3-5 words, Title Case, action-oriented
2. User Story MUST include [specific elements: ...] clause with actual named components from requirements
3. Each story should be 40-100 words
4. Deliverable descriptions should be 20-50 words with technical specifics
5. DO NOT create "Integration Testing" or other meta-stories
6. Split requirements using the split triggers above for proper granularity
7. Reference ACTUAL field names, sensors, components from requirements (no generic placeholders)
8. Generate ONE story per input requirement at minimum. Do NOT merge multiple requirements into one story.
9. If the input has N requirements, output at least N stories (more if split triggers apply)

BAD EXAMPLES (what NOT to do):
❌ Missing Title or vague Title:
"Title": "Collect Data From A Set" ← truncated, meaningless
"Title": "System Feature" ← too generic

❌ Missing [specific elements] clause:
"User Story": "The system must process data." ← No specific elements listed!

❌ Vague "so that" clause:
"User Story": "..., so that data is available." ← Available to whom? For what purpose?

❌ Generic placeholders instead of actual components:
"User Story": "The system must collect sensor data using [sensors], so that data is available." ← "sensors" is generic!

❌ Meta-story that shouldn't exist:
"User Story": "The system must include integration testing..." ← This is about testing methodology, not a feature!

GOOD EXAMPLES (correct format):

Example 1 - Patient Demographics:
{{
    "Title": "Record Patient Demographics",
    "User Story": "The patient information system must record patient demographics using [specific elements: name, address, age, next_of_kin], so that medical staff can retrieve complete patient profiles during consultations.",
    "Deliverables": {{
        "architecture_design": "Design of the patient demographics module with data entry forms, validation rules for the 4 required fields (name, address, age, next_of_kin), and storage interface.",
        "database_schema_design": "Schema with patients table containing fields [patient_id, name, address, age, next_of_kin, created_at, updated_at] with appropriate indexes and constraints.",
        "unit_tests": "Tests to verify all 4 demographic fields are captured, validated, stored, and retrievable with edge cases for missing/invalid data."
    }}
}}

Example 2 - Sensor Data Collection (demonstrates split):
Requirement: "The weather station must collect wind speed, temperature, and pressure data every 5 minutes and transmit to the server."
→ Split into 2 stories:

Story 1 - Data Collection:
{{
    "Title": "Collect Periodic Sensor Readings",
    "User Story": "The weather station must collect periodic readings using [specific elements: anemometer for wind_speed, thermometer for air_temperature, barometer for barometric_pressure] sampled every 5 minutes, so that accurate weather observations are available for downstream aggregation.",
    "Deliverables": {{
        "architecture_design": "Design of the data collection module with per-sensor driver interfaces (anemometer, thermometer, barometer), 5-minute scheduler, and local buffer for readings.",
        "database_schema_design": "Schema with readings table containing fields [reading_id, sensor_type, timestamp, value, unit, quality_flag] indexed by timestamp and sensor_type."
    }}
}}

Story 2 - Data Transmission:
{{
    "Title": "Transmit Compressed Sensor Packets",
    "User Story": "The weather station must transmit aggregated sensor readings using [specific elements: compressed data packets containing wind_speed, air_temperature, barometric_pressure readings] when satellite uplink is confirmed, so that the operations center receives complete observation sets with no data loss.",
    "Deliverables": {{
        "architecture_design": "Design of the transmission module with data aggregation, compression algorithm, uplink confirmation protocol, and retry mechanism for failed transmissions.",
        "error_handling": "Fault detection for transmission failures, local storage of unsent packets, automatic retry with exponential backoff, and alert generation for prolonged outages."
    }}
}}
"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", pp),
        ("user", "{input}")
    ])
    chain = _json_chain(prompt, chat, output_parser)
    re = chain.invoke({"input": requirements})
    return _strip_fences(re)

def refine_epics(epic:str,chat)->str:
    pp = """given the input epic and its deliverables, please generate definition of done for each deliverable.
         Your response should be in Json format. Respond with JSON only — no prose before or after."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", pp),
        ("user", "{input}")
    ])
    chain = _json_chain(prompt, chat, output_parser)
    re = chain.invoke({"input": epic})
    return _strip_fences(re)

def refine_epics_v2(epic:str,chat)->str:
    """Enhanced v2: Generates comprehensive Definition of Done arrays with specific deliverable-type guidance"""
    pp = """RESPOND WITH JSON ONLY. Do not include any prose, explanations, or text outside the JSON. Your entire response must be a single valid JSON object starting with { and ending with }.

You are a Definition of Done generator. Your job: take a user story with deliverables and return the SAME structure with each deliverable enriched by a "definition_of_done" array of 4-6 specific, actionable, measurable criteria.

IMPORTANT — OUTPUT SHAPE:
Return the full enriched story object. The top-level keys are "User Story" and "Deliverables".
Each deliverable becomes an object with "description" (preserved from input) and "definition_of_done" (array of strings you generate).

DELIVERABLE-TYPE GUIDANCE:

ARCHITECTURE_DESIGN DoD must include:
- Complete diagram of all named modules and their interactions
- Detailed design doc covering algorithms, data flow, and interfaces
- API/interface specs with data formats and error codes
- Error handling and fault-recovery mechanisms documented
- Design reviewed and signed off by technical lead

DATABASE_SCHEMA_DESIGN DoD must include:
- Schema listing specific tables/collections with all key fields enumerated [field1, field2, ...]
- Indexes, relationships, and constraints defined
- Migration scripts created and tested
- Schema review completed
- Special case: if the story has no persistence needs, write "N/A — no persistence in scope for this story"

API_ENDPOINTS DoD must include:
- All endpoints documented with request/response formats
- Authentication and authorization mechanisms defined
- Error codes and input validation rules specified
- API documentation generated (e.g., OpenAPI/Swagger)
- Contract tests passing for all endpoints

ERROR_HANDLING DoD must include:
- Fault detection implemented for all named failure modes
- Error logging with severity levels and context fields
- Recovery procedures defined, implemented, and tested
- Alert generated for critical failures with defined escalation path
- Graceful degradation behaviour verified under each failure scenario

UNIT_TESTS / INTEGRATION_TESTS DoD must include:
- Tests written for all named functions/workflows in the story
- All passing in the CI/CD pipeline with zero failures
- Edge cases and error conditions covered
- Test documentation completed with inputs and expected results

SECURITY_CONTROLS DoD must include:
- Authentication and authorisation implemented
- Input validation and sanitisation applied at all entry points
- Encryption confirmed for data at rest and in transit
- Security testing completed with no critical or high vulnerabilities

MONITORING_LOGGING DoD must include:
- Metrics and log events defined for all named components
- Alerts configured with thresholds and notification channels
- Dashboards created showing key health indicators
- Runbook written for common alert scenarios

CRITICAL RULES:
1. PRESERVE the "User Story" and "Title" fields exactly as provided — do not paraphrase or shorten
2. Each deliverable gets exactly 4-6 DoD items
3. Each DoD item: 15-35 words, specific and actionable
4. Reference the ACTUAL named components, fields, modules, or sensors from the user story
5. Do NOT invent numeric thresholds (%, ms, MB) unless they appear in the user story
6. "definition_of_done" MUST be a JSON array of strings, NOT a single string

EXAMPLE INPUT:
{{
    "User Story": "The insulin pump system must continuously monitor the user's blood sugar levels using [specific elements: implanted microsensor, glucose_level_calculator], so that the pump can detect hypoglycaemia and adjust insulin delivery within one reading cycle.",
    "Deliverables": {{
        "architecture_design": "Design of the continuous monitoring and glucose calculation modules.",
        "unit_tests": "Tests to verify microsensor data collection and glucose calculation accuracy."
    }}
}}

EXAMPLE OUTPUT:
{{
    "User Story": "The insulin pump system must continuously monitor the user's blood sugar levels using [specific elements: implanted microsensor, glucose_level_calculator], so that the pump can detect hypoglycaemia and adjust insulin delivery within one reading cycle.",
    "Deliverables": {{
        "architecture_design": {{
            "description": "Design of the continuous monitoring and glucose calculation modules.",
            "definition_of_done": [
                "Architecture diagram showing monitoring_module, glucose_level_calculator, and microsensor_interface with all data-flow paths documented",
                "Design doc for monitoring_module specifying sampling frequency, data acquisition protocol from implanted microsensor, and buffer management",
                "Design doc for glucose_level_calculator specifying the algorithm that converts raw microsensor readings to mmol/L glucose values",
                "API specification for the interface between monitoring_module and glucose_level_calculator including data format and error codes",
                "Failure modes documented for microsensor disconnection, out-of-range readings, and calculation errors with defined recovery actions",
                "Design reviewed and approved by technical lead and medical safety officer"
            ]
        }},
        "unit_tests": {{
            "description": "Tests to verify microsensor data collection and glucose calculation accuracy.",
            "definition_of_done": [
                "Unit tests written for microsensor_read(), glucose_level_calculator.calculate(), and monitoring_module.poll() covering all normal execution paths",
                "Tests verify continuous polling produces readings with no skipped cycles under normal operating conditions",
                "Tests confirm glucose_level_calculator produces correct mmol/L output from known raw microsensor inputs",
                "Edge-case tests covering microsensor disconnection, saturated readings, and calculator divide-by-zero scenarios",
                "All tests passing in CI/CD pipeline with zero failures",
                "Test documentation completed listing each test case, its inputs, and expected output"
            ]
        }}
    }}
}}

BAD EXAMPLES (too generic — never produce these):
❌ "Design is complete"
❌ "Tests pass"
❌ "90% code coverage" — only if the requirement explicitly states 90%

GOOD EXAMPLES (specific, using actual names from the story):
✅ "Architecture diagram showing monitoring_module, glucose_level_calculator, and microsensor_interface with all data-flow paths"
✅ "Unit tests for microsensor_read(), glucose_level_calculator.calculate() covering happy path and 4 error scenarios (disconnected, saturated, null, negative)"
✅ "All tests passing in CI/CD pipeline with zero failures and no deprecation warnings"
"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", pp),
        ("user", "{input}")
    ])
    chain = _json_chain(prompt, chat, output_parser)
    re = chain.invoke({"input": epic})
    return _strip_fences(re)

def generate_test_cases(requirements:str,chat, mode)->str:
    pp = """given the input software requirements,please generate test cases for each requirement that we can use to
    verify the completeness of those requirements.
         Your response should be in Json format. Respond with JSON only — no prose before or after."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", pp),
        ("user", "{input}")
    ])
    chain = _json_chain(prompt, chat, output_parser)
    re = chain.invoke({"input": requirements})
    return _strip_fences(re)

def generate_test_cases_v2(requirements:str,chat, mode)->str:
    """Enhanced v2: Generates detailed, globally-numbered test cases with concrete expected results"""
    pp = """RESPOND WITH JSON ONLY. Do not include any prose, explanations, or text outside the JSON. Your entire response must be a single valid JSON object starting with { and ending with }.

You are an automated test case generator. Generate comprehensive, executable test cases for each requirement.

MATCHING RULE — CRITICAL:
The "requirement" field in each output object MUST be copied WORD-FOR-WORD from the input.
Do NOT paraphrase, summarise, or reword. The exact text is used to link test cases back to their user story.

GLOBAL TEST CASE NUMBERING (CRITICAL):
- TC numbering is GLOBAL and CONTINUOUS across ALL requirements: TC1, TC2, TC3 ... never restart
- If requirement 1 uses TC1–TC3, requirement 2 MUST start at TC4
- NEVER reuse a TC number; NEVER duplicate test case content

OUTPUT FORMAT:
{{
  "test_cases": [
    {{
      "requirement": "<EXACT word-for-word copy of the user story text from the input>",
      "test_cases": [
        {{
          "id": "TC1",
          "description": "Verify that [specific named component] [specific action] under [specific conditions] as described in the requirement",
          "steps": [
            "Step 1: [concrete action using actual field names / values / component names from the requirement]",
            "Step 2: [concrete action]",
            "Step 3: [measurement or observation step]"
          ],
          "expected_result": "Concrete, verifiable outcome using actual field names, states, or values from the requirement. NO invented metrics."
        }},
        {{
          "id": "TC2",
          "description": "Test negative / edge case: [specific element from requirement] when [specific failure condition]",
          "steps": ["..."],
          "expected_result": "Specific error message, state change, or recovery behaviour implied by the requirement"
        }}
      ]
    }}
  ]
}}

CRITICAL RULES:
1. "requirement" field = EXACT COPY of the input user story text, word-for-word.
2. GLOBAL TC NUMBERING: TC1, TC2, TC3 ... across ALL requirements. Never restart per requirement.
3. CONCRETE EXPECTED RESULTS — use actual field names, values, states from the requirement:
   ✅ "All 4 fields (name, address, age, next_of_kin) stored and retrievable from the patients table"
   ✅ "System emits fault alert to Fleet Operations Center within one polling cycle"
   ❌ "Data is correct" — too vague
   ❌ "System works as expected" — too vague
   ❌ "Response within 2 seconds" — invented metric; only include if the requirement states it
4. NO INVENTED METRICS: omit percentages, time limits, accuracy thresholds unless the requirement explicitly states them.
   If you must infer, tag it: "[Assumed: …]"
5. UNIQUE TEST CASES: each requirement tests its OWN specific functionality.
   Do NOT copy the same test description to multiple requirements.
6. REQUIREMENT-SPECIFIC: test steps must name the ACTUAL sensors, fields, components, or actors from that requirement.
   "anemometer, wind_speed, barometric_pressure" not "sensor", "data", "values".
7. Each requirement: 2–3 test cases — at minimum 1 happy path + 1 negative/edge case.

GOOD EXAMPLE (global numbering + concrete results + exact requirement copy):
{{
  "test_cases": [
    {{
      "requirement": "The patient information system must record patient demographics using [specific elements: name, address, age, next_of_kin], so that medical staff can retrieve complete patient profiles during consultations.",
      "test_cases": [
        {{
          "id": "TC1",
          "description": "Verify all 4 demographic fields (name, address, age, next_of_kin) are captured and persisted when a patient record is created",
          "steps": [
            "Create a new patient record supplying name='John Doe', address='123 Main St', age=45, next_of_kin='Jane Doe'",
            "Submit the patient record creation request",
            "Retrieve the stored record from the patients table",
            "Verify all 4 fields match the submitted values exactly"
          ],
          "expected_result": "All 4 fields (name, address, age, next_of_kin) stored in the patients table and returned unchanged on retrieval"
        }},
        {{
          "id": "TC2",
          "description": "Test validation when required field (name) is absent from a patient record creation request",
          "steps": [
            "Submit a patient record creation request with address, age, and next_of_kin but no name field",
            "Observe system response"
          ],
          "expected_result": "Validation error returned indicating 'name field is required'; record not persisted in the patients table"
        }}
      ]
    }},
    {{
      "requirement": "The system must generate monthly management reports showing clinic activity and patient statistics.",
      "test_cases": [
        {{
          "id": "TC3",
          "description": "Verify the monthly management report includes clinic activity data for a month with existing records",
          "steps": [
            "Ensure the database contains patient and appointment records for January 2024",
            "Request a monthly management report for January 2024",
            "Inspect the report output"
          ],
          "expected_result": "Report contains clinic activity and patient statistics sections populated with data matching the database records for January 2024"
        }},
        {{
          "id": "TC4",
          "description": "Test report generation for a month with no existing data",
          "steps": [
            "Select a month with no patient or appointment records",
            "Request the monthly management report for that month",
            "Inspect the report output"
          ],
          "expected_result": "Report is generated successfully with all metric sections showing zero counts; no error or crash"
        }}
      ]
    }}
  ]
}}

BAD EXAMPLES (never do these):
❌ Paraphrased requirement field:
"requirement": "Record patient data"  ← should be the full word-for-word user story text

❌ Restarted TC numbering:
Requirement 1 test_cases: TC1, TC2
Requirement 2 test_cases: TC1, TC2  ← WRONG, must be TC3, TC4

❌ Vague expected result:
"expected_result": "System works correctly"

❌ Invented metric:
"expected_result": "Response time under 500ms"  ← only if requirement states this

❌ Duplicate description across requirements:
Req 1: "Verify patient record creation"
Req 2: "Verify patient record creation"  ← WRONG, test the specific functionality of req 2
"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", pp),
        ("user", "{input}")
    ])
    chain = _json_chain(prompt, chat, output_parser)
    re = chain.invoke({"input": requirements})
    return _strip_fences(re)

def rat(refine, thought, x,chat, mode="prod"):
    prompt = (PromptTemplate.from_template("""As a voter, you vote for the input that is more accurate, concise and easy
                                           to understand. Given two input texts, the first:\n
                                        {input_first}\n and the second:\n" {input_second}\n", which one you vote for?
                                           Please only answer with your vote."""))

    x1 = refine(x, chat,mode)
    if mode == "debug":
        print("Refine successfully:\n")
        print("=============================\n")
        print(x1)
        print("=============================\n")
    
    # Use LangChain's LCEL (modern syntax)
    chain = prompt | chat | output_parser
    re_text = chain.invoke({"input_first":x, "input_second":x1})
    
    if mode == "debug":
        print(re_text)
    
    better = None
    if '1' in re_text.lower() or 'first' in re_text.lower():
        better = x
    elif '2' in re_text.lower() or 'second' in re_text.lower():
        better = x1
    else:
        # Default to refined version if unclear
        better = x1
    
    x2 = thought(better, chat, mode)
    return x2

def get_epics(deliverables: str, chat)->str:
    just_tasks = json.loads(deliverables)
    _key = "Epics"
    new_key = "User Stories"
    _key_2 = "Deliverables"
    refine_tasks = {new_key: []}
    for epic in just_tasks[_key]:
        try:
            enriched = json.loads(refine_epics(epic, chat))
            epic[_key_2] = enriched.get(_key_2, enriched)
        except (json.JSONDecodeError, KeyError):
            pass  # keep original deliverables if LLM returns malformed JSON
        refine_tasks[new_key].append(epic)
    return json.dumps(refine_tasks, indent=4)

def get_epics_v2(deliverables: str, chat)->str:
    """Improved version using refine_epics_v2 for detailed Definition of Done"""
    just_tasks = json.loads(deliverables)
    _key = "Epics"
    new_key = "User Stories"
    _key_2 = "Deliverables"
    refine_tasks = {new_key: []}
    for epic in just_tasks[_key]:
        try:
            enriched = json.loads(refine_epics_v2(epic, chat))
            epic[_key_2] = enriched.get(_key_2, enriched)
        except (json.JSONDecodeError, KeyError):
            pass  # keep original deliverables if LLM returns malformed JSON
        refine_tasks[new_key].append(epic)
    return json.dumps(refine_tasks, indent=4)

def filter_meta_stories(stories_json: str) -> str:
    """
    Removes meta-level stories that describe testing/documentation methodology rather than features.

    Meta-stories are about HOW the system is validated/documented, not WHAT the system does.
    Examples: "Integration Testing", "Documentation", "Testing Coverage", "Quality Assurance"

    Args:
        stories_json: JSON string with User Stories

    Returns:
        JSON string with meta-stories removed
    """
    try:
        stories = json.loads(stories_json)
    except json.JSONDecodeError:
        return stories_json

    # Meta-story patterns to filter out
    meta_patterns = [
        "integration testing",
        "integration test",
        "documentation",
        "testing coverage",
        "test coverage",
        "quality assurance",
        "qa process",
        "testing strategy",
        "testing methodology",
        "test automation",
        "continuous integration",
        "ci/cd pipeline"
    ]

    # Get the user stories list (could be under "User Stories" or "Epics" key)
    user_stories_key = "User Stories" if "User Stories" in stories else "Epics"
    user_stories = stories.get(user_stories_key, [])

    filtered_stories = []
    removed_count = 0

    for story in user_stories:
        # Get the user story text (could be "User Story" field)
        story_text = story.get("User Story", "").lower()

        # Check if story matches any meta-pattern
        is_meta = False
        for pattern in meta_patterns:
            if pattern in story_text:
                print(f"[FILTER] Removing meta-story: {story.get('User Story', 'Unknown')[:100]}")
                is_meta = True
                removed_count += 1
                break

        if not is_meta:
            filtered_stories.append(story)

    if removed_count > 0:
        print(f"[FILTER] Removed {removed_count} meta-level stories (testing/documentation methodology)")

    stories[user_stories_key] = filtered_stories
    return json.dumps(stories, indent=4)
