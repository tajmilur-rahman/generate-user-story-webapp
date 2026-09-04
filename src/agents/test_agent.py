from .base_agent import BaseAgent
from typing import Dict, Any

class TestCaseAgent(BaseAgent):
    """Generates test cases - replaces generate_test_cases_v2"""

    def __init__(self):
        super().__init__(
            name="Test Case Generator",
            role="QA Test Engineer",
            goal="Generate comprehensive test cases covering all scenarios"
        )

    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        requirements_batch = context.get('requirements_batch', [])
        starting_tc_number = context.get('starting_tc_number', 1)

        reqs_text = "\n".join([
            f"- {req['id']}: {req['description']}"
            for req in requirements_batch
        ])

        return f"""RESPOND WITH JSON ONLY. Do not include any prose, explanations, markdown headers, or text outside the JSON. Your entire response must be a single valid JSON object starting with {{{{ and ending with }}}}.

You are a QA Test Engineer generating comprehensive, executable test cases for requirements.

REQUIREMENTS TO TEST:
{reqs_text}

GLOBAL TEST CASE NUMBERING (CRITICAL):
- Start numbering from TC{starting_tc_number}
- TC numbering is GLOBAL and CONTINUOUS across ALL requirements
- Never restart numbering per requirement
- Never reuse a TC number
- Never duplicate test case content

COVERAGE REQUIREMENTS:
Each requirement needs 2-4 test cases covering:
1. Happy path: normal successful flow with valid inputs
2. Edge case: boundary conditions, empty inputs, maximum limits
3. Error scenario: invalid inputs, system failures, recovery
4. Additional scenario: recovery, integration, or performance (optional based on requirement complexity)

TEST CASE REQUIREMENTS:
1. Test ID: Sequential global numbering (TC{starting_tc_number}, TC{starting_tc_number+1}, ...)
2. Description: "Verify that [specific component] [specific action] under [specific conditions]"
3. Steps: Concrete actions using actual field names/values/components from requirement
4. Expected Result: Specific, verifiable outcome using actual field names and states

CONCRETE EXPECTED RESULTS RULES:
- Use ACTUAL field names, values, states from the requirement
- ✅ GOOD: "All 4 fields (name, address, age, next_of_kin) stored in patients table and retrievable"
- ✅ GOOD: "System emits fault alert to operations center within one polling cycle"
- ❌ BAD: "Data is correct" — too vague
- ❌ BAD: "System works as expected" — too vague
- ❌ BAD: "Response within 2 seconds" — invented metric (only include if requirement states it)

NO INVENTED METRICS:
- Do NOT add percentages, time limits, accuracy thresholds unless the requirement explicitly states them
- If you must infer, tag it: "[Assumed: ...]"

UNIQUE TEST CASES:
- Each requirement tests its OWN specific functionality
- Do NOT copy-paste the same test description to multiple requirements
- Test steps must name ACTUAL sensors, fields, components from that requirement

OUTPUT FORMAT (JSON only):
{{{{
  "test_cases": [
    {{{{
      "test_id": "TC{starting_tc_number}",
      "requirement_id": "REQ-001",
      "test_description": "Verify temperature readings are recorded automatically every 5 minutes with timestamp and sensor ID",
      "test_steps": [
        "Power on the weather station with thermometer sensor connected",
        "Wait for 5 minutes",
        "Query the readings table for new temperature records",
        "Verify the record contains sensor_id, timestamp, and temperature_value fields",
        "Wait another 5 minutes and verify a second record appears"
      ],
      "expected_result": "New temperature reading recorded in readings table with fields: sensor_id, timestamp, temperature_value. Readings appear exactly 5 minutes apart based on timestamp comparison"
    }}}},
    {{{{
      "test_id": "TC{starting_tc_number+1}",
      "requirement_id": "REQ-001",
      "test_description": "Verify system handles thermometer sensor disconnection gracefully",
      "test_steps": [
        "Power on weather station with sensor connected",
        "Wait for one successful recording (5 minutes)",
        "Disconnect thermometer sensor",
        "Wait for next 5-minute interval",
        "Check error log and readings table"
      ],
      "expected_result": "Error logged with message 'Thermometer sensor disconnected', no reading recorded in readings table for that interval, system continues attempting to read every 5 minutes"
    }}}},
    {{{{
      "test_id": "TC{starting_tc_number+2}",
      "requirement_id": "REQ-001",
      "test_description": "Verify temperature readings outside normal range are flagged",
      "test_steps": [
        "Configure thermometer sensor to return temperature_value = -60 Celsius (below normal range)",
        "Wait for 5-minute recording interval",
        "Query readings table for the new record",
        "Check the quality_flag field"
      ],
      "expected_result": "Reading recorded with temperature_value = -60 and quality_flag set to 'out_of_range', system continues normal operation"
    }}}}
  ]
}}}}

CRITICAL RULES:
1. Start TC numbering from TC{starting_tc_number} and increment continuously
2. 2-4 test cases per requirement (minimum: happy path + error case, add edge/recovery cases as needed)
3. Test descriptions: specific to the requirement, not generic
4. Test steps: use actual field names, sensors, components from requirement
5. Expected results: concrete, using actual field/table names, no vague statements
6. NO invented metrics unless stated in requirement
7. Each test case must be unique (no copy-paste across requirements)
8. NEVER OUTPUT PLACEHOLDERS: NEVER output "-" or "N/A" or "TBD" for test cases.
   Every requirement MUST have at least 2 test cases (1 happy path + 1 negative/edge case).
   If you are unsure about test details, generate basic tests:
   ✅ Happy path: "Verify the requirement's main functionality works correctly."
   ✅ Edge case: "Verify the system handles invalid input or failure conditions."
   ❌ NEVER output: "-", "N/A", "TBD", "No test cases", "See requirement"

BAD EXAMPLES (what NOT to do):
❌ Generic description:
"Verify system works correctly" — what specifically?

❌ Vague expected result:
"Data is correct", "System behaves as expected"

❌ Invented metric:
"Response time under 500ms" — only if requirement mentions this

❌ Generic test steps:
"Test the feature", "Verify it works"

❌ Copy-paste across requirements:
Using identical test description for REQ-001 and REQ-002

GOOD EXAMPLES (correct format):
✅ Specific description:
"Verify all 4 demographic fields (name, address, age, next_of_kin) are captured and persisted when patient record is created"

✅ Concrete expected result:
"Record created in patients table with patient_id, name='John Doe', address='123 Main St', age=45, next_of_kin='Jane Doe'. All 4 fields retrievable via query"

✅ Specific test steps:
"Create new patient record supplying name='John Doe', address='123 Main St', age=45, next_of_kin='Jane Doe'"
"Submit the patient creation request via POST /api/patients"
"Query patients table with patient_id returned from creation"

✅ Requirement-specific tests:
REQ-001 (temperature): test temperature_value, thermometer sensor, Celsius
REQ-002 (humidity): test humidity_value, hygrometer sensor, percentage

RESPOND WITH JSON ONLY."""
