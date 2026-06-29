import os
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
        ("system", """You are an software engineer to develop the functional requirements from the given software product
         design document. Integration testing is always one of the requirements. Your response should only have the list of the functional requirements."""),
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
        ("system", """You are the project manager who will refine the given functional requirements to combine redundant
         requirements and add missing requirements according to the existed one.
         Your response should only have the list of the refined functional requirements."""),
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
    chain = prompt | chat | output_parser
    re = chain.invoke({"input": requirements})
    return re.replace("json","").replace("```","")

def extract_epics_v2(requirements:str,chat, mode)->str:
    """Enhanced v2: Creates detailed user stories with specific elements clause and proper decomposition"""
    pp = """You are an automated requirements-to-user-story engine. Generate detailed, engineering-ready user stories.

USER STORY FORMAT (MANDATORY):
The <system/actor> must <capability> using [specific elements: <concrete items, fields, instruments, parameters, or thresholds taken verbatim from the requirements>], so that <business/engineering value>.

The [specific elements: ...] clause is MANDATORY. It must list the actual components, fields, sensors, data items, or parameters mentioned in the requirement.

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
            "User Story": "The <system> must <capability> using [specific elements: <field1, field2, sensor3, parameter4>], so that <value>.",
            "Deliverables": {{
                "architecture_design": "Design of the <specific module names> including <specific components: algorithms, interfaces, workflows> to enable <specific functionality>.",
                "database_schema_design": "Schema with tables <table1, table2> containing fields [field1, field2, field3] to support <specific operations>.",
                "unit_tests": "Tests to verify <specific component> correctly <specific behavior> with <specific scenarios>."
            }}
        }}
    ]
}}

CRITICAL RULES:
1. User Story MUST include [specific elements: ...] clause with actual components from requirements
2. Each story should be 40-100 words
3. Deliverable descriptions should be 20-50 words with technical specifics
4. DO NOT create "Integration Testing" or other meta-stories
5. Split requirements using the split triggers above for proper granularity
6. Reference ACTUAL field names, sensors, components from requirements (no generic placeholders)

BAD EXAMPLES (what NOT to do):
❌ Missing [specific elements] clause:
"User Story": "The system must process data." ← No specific elements listed!

❌ Generic placeholders instead of actual components:
"User Story": "The system must collect sensor data using [sensors], so that data is available." ← "sensors" is generic!

❌ Meta-story that shouldn't exist:
"User Story": "The system must include integration testing..." ← This is about testing methodology, not a feature!

GOOD EXAMPLES (correct format):

Example 1 - Patient Demographics:
{{
    "User Story": "The patient information system must record patient demographics using [specific elements: name, address, age, next_of_kin], so that complete patient profiles can be maintained for medical staff access.",
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
    "User Story": "The weather station must collect periodic readings using [specific elements: anemometer for wind_speed, thermometer for air_temperature, barometer for barometric_pressure] sampled every 5 minutes, so that accurate weather observations are available for aggregation.",
    "Deliverables": {{
        "architecture_design": "Design of the data collection module with per-sensor driver interfaces (anemometer, thermometer, barometer), 5-minute scheduler, and local buffer for readings.",
        "database_schema_design": "Schema with readings table containing fields [reading_id, sensor_type, timestamp, value, unit, quality_flag] indexed by timestamp and sensor_type."
    }}
}}

Story 2 - Data Transmission:
{{
    "User Story": "The weather station must transmit aggregated sensor readings using [specific elements: compressed data packets containing wind_speed, air_temperature, barometric_pressure readings] when satellite uplink is confirmed, so that data reaches the operations center reliably.",
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
    chain = prompt | chat | output_parser
    re = chain.invoke({"input": requirements})
    return re.replace("json","").replace("```","")

def refine_epics(epic:str,chat)->str:
    pp = """given the input epic and its deliverables, please generate definition of done for each deliverable.
         Your response should be in Json format."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", pp),
        ("user", "{input}")
    ])
    chain = prompt | chat | output_parser
    re = chain.invoke({"input": epic})
    return re.replace("json","").replace("```","")

def refine_epics_v2(epic:str,chat)->str:
    """Enhanced v2: Generates comprehensive Definition of Done arrays with specific deliverable-type guidance"""
    pp = """You are a Definition of Done generator. For each deliverable, create 4-6 specific, actionable, measurable DoD criteria.

Each deliverable type has specific requirements:

ARCHITECTURE DESIGN DoD must include:
- Complete system/component diagram showing all modules and interactions
- Detailed design document describing algorithms, data flow, interfaces
- API/interface specifications with data formats and error codes
- Error handling and fault recovery mechanisms
- Design review and approval sign-off

DATABASE/DATA SCHEMA DESIGN DoD must include:
- Schema design with specific tables/collections listed
- All key fields enumerated [field1, field2, field3...]
- Indexes, relationships, and constraints defined
- Migration scripts created and tested
- Schema review and approval
- Special case: If story has NO persistence needs, write "N/A — no persistence in scope for this story"

API/INTERFACE CONTRACT DoD must include:
- API endpoints documented (request/response formats)
- Authentication and authorization mechanisms defined
- Error codes and validation rules specified
- Rate limiting and security controls implemented
- API documentation generated (OpenAPI/Swagger)

ERROR HANDLING & FAULT REPORTING DoD must include:
- Fault detection mechanisms implemented
- Error logging with severity levels and context
- Recovery procedures defined and tested
- Alert generation for critical failures
- Graceful degradation behavior verified

SECURITY CONTROLS DoD must include:
- Authentication and authorization implemented
- Input validation and sanitization added
- Encryption for data at rest and in transit
- Security testing completed (no critical vulnerabilities)
- Compliance with relevant standards verified

UNIT TESTS / INTEGRATION TESTS DoD must include:
- Tests written for all core functions/workflows
- Code coverage meets minimum threshold (specify %, e.g., 80%)
- All tests passing in CI/CD pipeline
- Edge cases and error conditions tested
- Test documentation completed

CRITICAL RULES:
1. PRESERVE the User Story text exactly as provided
2. Each deliverable gets 4-6 DoD items (not more, not less)
3. DoD items must be 15-30 words (detailed enough to be actionable)
4. Reference SPECIFIC technical details from the user story (actual component names, field names, modules)
5. Be CONCRETE (avoid "ensure quality", "test thoroughly")
6. Include measurable criteria where possible (percentages, counts, standards)
7. Output format: "definition_of_done" as an ARRAY, not a string

EXAMPLE INPUT:
{{
    "User Story": "The insulin pump system must continuously monitor the user's blood sugar levels using an implanted microsensor and accurately calculate the blood sugar level from the data provided.",
    "Deliverables": {{
        "architecture_design": "Design of the continuous monitoring and data calculation modules within the insulin pump system.",
        "unit_tests": "Tests to ensure the microsensor's data collection and blood sugar calculation accuracy."
    }}
}}

EXAMPLE OUTPUT:
{{
    "User Story": "The insulin pump system must continuously monitor the user's blood sugar levels using an implanted microsensor and accurately calculate the blood sugar level from the data provided.",
    "Deliverables": {{
        "architecture_design": {{
            "description": "Design of the continuous monitoring and data calculation modules within the insulin pump system.",
            "definition_of_done": [
                "Complete system architecture diagram showing monitoring module, data calculation module, and sensor interface with all component interactions",
                "Detailed design document for blood sugar monitoring module including sensor data acquisition specifications and sampling frequency",
                "Detailed design document for blood sugar calculation module including algorithms for converting electrical conductivity to glucose levels",
                "Data flow diagrams showing how sensor readings move through the system to calculation output",
                "API specifications for all module interfaces including data formats and error codes",
                "Error handling and failover mechanisms documented for sensor disconnection and data corruption scenarios",
                "Design reviewed and approved by technical lead and medical safety officer"
            ]
        }},
        "unit_tests": {{
            "description": "Tests to ensure the microsensor's data collection and blood sugar calculation accuracy.",
            "definition_of_done": [
                "Unit tests written for all monitoring functions achieving minimum 90% code coverage",
                "Tests verify sensor data reading occurs continuously without gaps or interruptions",
                "Tests validate correct blood sugar calculation from sensor electrical conductivity readings",
                "Tests confirm calculation accuracy within required medical standards (±5% margin)",
                "Edge case tests for sensor malfunction, data corruption, and communication failures",
                "All tests passing in CI/CD pipeline with zero failures",
                "Test documentation completed with test case descriptions, inputs, and expected results"
            ]
        }}
    }}
}}

OUTPUT SCHEMA:
{{
    "User Story": "<preserve exactly from input>",
    "Deliverables": {{
        "<deliverable_name>": {{
            "description": "<preserve from input>",
            "definition_of_done": [
                "<DoD item 1: 15-30 words, specific and actionable>",
                "<DoD item 2: 15-30 words, specific and actionable>",
                "<DoD item 3: 15-30 words, specific and actionable>",
                "<DoD item 4: 15-30 words, specific and actionable>",
                "<DoD item 5 (optional): 15-30 words, specific and actionable>",
                "<DoD item 6 (optional): 15-30 words, specific and actionable>"
            ]
        }}
    }}
}}

BAD EXAMPLES (too generic):
❌ "Design is complete" ← No specifics! What design? Complete how?
❌ "Tests pass" ← Which tests? What criteria?
❌ "90% code coverage" ← Only if the requirement specifies 90%! Otherwise it's invented.

GOOD EXAMPLES (specific with actual components):
✅ "Complete architecture diagram showing monitoring_module, calculation_module, and sensor_interface with all component interactions documented"
✅ "Database schema designed with patients table containing fields [patient_id, name, address, age, next_of_kin, created_at] with indexes on patient_id and created_at"
✅ "Unit tests written for patient_create(), patient_update(), patient_retrieve() functions covering happy path and 5 edge cases (missing name, invalid age, duplicate patient_id, null next_of_kin, SQL injection attempt)"
✅ "All tests passing in CI/CD pipeline with zero failures and no deprecated warnings"

Remember:
- Output "definition_of_done" as an ARRAY of strings, not a single string
- 4-6 items per deliverable
- Reference ACTUAL component/field names from the user story
- Be SPECIFIC and MEASURABLE
"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", pp),
        ("user", "{input}")
    ])
    chain = prompt | chat | output_parser
    re = chain.invoke({"input": epic})
    return re.replace("json","").replace("```","")

def generate_test_cases(requirements:str,chat, mode)->str:
    pp = """given the input software requirements,please generate test cases for each requirement that we can use to
    verify the completeness of those requirements.
         Your response should be in Json format."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", pp),
        ("user", "{input}")
    ])
    chain = prompt | chat | output_parser
    re = chain.invoke({"input": requirements})
    return re.replace("json","").replace("```","")

def generate_test_cases_v2(requirements:str,chat, mode)->str:
    """Enhanced v2: Generates detailed, globally-numbered test cases with concrete expected results"""
    pp = """You are an automated test case generator. Generate comprehensive, executable test cases for each requirement.

GLOBAL TEST CASE NUMBERING (CRITICAL):
- Test case numbering (TC1, TC2, TC3...) is GLOBAL and CONTINUOUS across ALL requirements in the input
- NEVER restart numbering per requirement
- NEVER reuse a TC number
- NEVER duplicate test case content across requirements
- Each requirement gets its own UNIQUE test cases that test ONLY that requirement's functionality

OUTPUT FORMAT:
{{
  "test_cases": [
    {{
      "requirement": "Copy the exact requirement text being tested here (word-for-word from input)",
      "test_cases": [
        {{
          "id": "TC1",
          "description": "Verify that [specific component from requirement] [specific action from requirement] under [specific conditions from requirement]",
          "steps": [
            "Step 1: Specific action with actual field names, values, or components from the requirement",
            "Step 2: Another actionable step referencing specific elements from the requirement",
            "Step 3: Measurement step using actual metrics, thresholds, or criteria from the requirement"
          ],
          "expected_result": "Concrete, measurable outcome using actual values, field names, or states from the requirement. NO invented metrics."
        }},
        {{
          "id": "TC2",
          "description": "Test negative/edge case for [specific element from requirement]",
          "steps": [...],
          "expected_result": "Specific error message, state, or recovery behavior described in or implied by the requirement"
        }}
      ]
    }},
    {{
      "requirement": "Next requirement text...",
      "test_cases": [
        {{
          "id": "TC3",
          "description": "...",
          ...
        }}
      ]
    }}
  ]
}}

CRITICAL RULES:
1. GLOBAL TC NUMBERING: TC1, TC2, TC3... across ALL requirements. If requirement 1 ends at TC3, requirement 2 starts at TC4.
2. CONCRETE EXPECTED RESULTS: Use actual field names, values, states, error codes from the requirements document.
   - ✅ GOOD: "All 6 fields (name, address, age, next_of_kin, medical_history, allergies) populated from source"
   - ✅ GOOD: "Error code 404 returned with message 'Patient not found'"
   - ❌ BAD: "Data is correct" (vague)
   - ❌ BAD: "System works as expected" (generic)
   - ❌ BAD: "Response within 5% margin" (invented metric not in requirement)
3. NO INVENTED METRICS: Do NOT add percentages, time intervals, accuracy thresholds unless explicitly stated in the requirement.
   - If you must infer a metric, tag it: "[Assumption: response time <2s]"
4. UNIQUE TEST CASES: Each requirement gets DIFFERENT test cases testing DIFFERENT functionality.
   - ❌ BAD: Copy-pasting "verify patient record creation" test case to 5 different requirements
   - ✅ GOOD: "Verify management report generation" for reporting requirement, "Verify patient confidentiality" for security requirement
5. REQUIREMENT-SPECIFIC: Test cases must reference the SPECIFIC components, fields, instruments, or parameters mentioned in that requirement.
   - If requirement mentions "anemometer, wind speed, barometric pressure", test case must test THOSE specific sensors
   - If requirement mentions "name, address, age, next of kin", test case must verify THOSE specific fields
6. Each requirement should have 2-3 test cases: at least 1 positive (happy path) and 1 negative/edge case

GOOD EXAMPLE (demonstrates global numbering and concrete results):
{{
  "test_cases": [
    {{
      "requirement": "The patient information system must record patient demographics including name, address, age, and next of kin.",
      "test_cases": [
        {{
          "id": "TC1",
          "description": "Verify that all 4 demographic fields (name, address, age, next_of_kin) are captured and stored when creating a patient record",
          "steps": [
            "Create a new patient record with test data for all 4 fields: name='John Doe', address='123 Main St', age=45, next_of_kin='Jane Doe'",
            "Submit the patient record creation form",
            "Retrieve the stored patient record from the database",
            "Verify each field matches the input data exactly"
          ],
          "expected_result": "All 4 fields (name, address, age, next_of_kin) populated with exact input values and retrievable from database"
        }},
        {{
          "id": "TC2",
          "description": "Test validation when required demographic field (name) is missing",
          "steps": [
            "Attempt to create patient record with address='123 Main St', age=45, next_of_kin='Jane Doe' but omit name field",
            "Submit the form",
            "Observe system response"
          ],
          "expected_result": "Validation error displayed indicating 'name field is required' and record creation blocked"
        }}
      ]
    }},
    {{
      "requirement": "The system must generate monthly management reports showing clinic activity and patient statistics.",
      "test_cases": [
        {{
          "id": "TC3",
          "description": "Verify that monthly report includes clinic activity metrics (patient count, appointment count, treatment count)",
          "steps": [
            "Configure report date range for January 2024 (full month)",
            "Generate the monthly management report",
            "Review report contents for required metrics",
            "Verify metrics match database query results for same period"
          ],
          "expected_result": "Report displays 3 metrics (patient_count, appointment_count, treatment_count) matching database totals for January 2024"
        }},
        {{
          "id": "TC4",
          "description": "Test report generation when no data exists for selected month",
          "steps": [
            "Select a future month with no patient data (e.g., December 2025)",
            "Generate the report",
            "Review report output"
          ],
          "expected_result": "Report displays with all metric counts = 0 and message 'No data available for selected period'"
        }}
      ]
    }}
  ]
}}

BAD EXAMPLES (what NOT to do):
❌ Restarting TC numbering per requirement:
{{
  "requirement": "Record patient data",
  "test_cases": [{{ "id": "TC1", ... }}]
}},
{{
  "requirement": "Generate reports",
  "test_cases": [{{ "id": "TC1", ... }}]  ← WRONG! Should be TC3
}}

❌ Vague expected results:
"expected_result": "System works correctly"  ← No! What specific behavior?
"expected_result": "Data is accurate"  ← No! Which fields? What values?

❌ Invented metrics not in requirement:
"expected_result": "Response time under 2 seconds"  ← Only if requirement specifies 2s!
"expected_result": "95% accuracy"  ← Only if requirement specifies 95%!

❌ Duplicate test cases across requirements:
Requirement 1: "Verify patient record creation" ← OK
Requirement 2: "Verify patient record creation" ← WRONG! Different requirement needs different test!

Remember:
- TC numbers are GLOBAL and CONTINUOUS (TC1, TC2, TC3... never restart)
- Use ACTUAL field names, values, states from the requirement
- NO invented percentages, times, or thresholds
- Each requirement gets UNIQUE tests for ITS specific functionality
"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", pp),
        ("user", "{input}")
    ])
    chain = prompt | chat | output_parser
    re = chain.invoke({"input": requirements})
    return re.replace("json","").replace("```","")

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
    _key_2="Deliverables"
    refine_tasks = {new_key:[]}
    for epic in just_tasks[_key]:
        new_devs = json.loads(refine_epics(epic, chat))
        epic[_key_2] = new_devs
        refine_tasks[new_key].append(epic)
    epics = json.dumps(refine_tasks, indent=4)
    return epics

def get_epics_v2(deliverables: str, chat)->str:
    """Improved version using refine_epics_v2 for detailed Definition of Done"""
    just_tasks = json.loads(deliverables)
    _key = "Epics"
    new_key = "User Stories"
    _key_2="Deliverables"
    refine_tasks = {new_key:[]}
    for epic in just_tasks[_key]:
        new_devs = json.loads(refine_epics_v2(epic, chat))
        epic[_key_2] = new_devs
        refine_tasks[new_key].append(epic)
    epics = json.dumps(refine_tasks, indent=4)
    return epics

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
