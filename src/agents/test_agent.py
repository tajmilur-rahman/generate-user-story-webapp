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

        reqs_text = "\n".join([
            f"- {req['id']}: {req['description']}"
            for req in requirements_batch
        ])

        return f"""RESPOND WITH JSON ONLY. Do not include any prose, explanations, markdown headers, or text outside the JSON. Your entire response must be a single valid JSON object starting with {{{{ and ending with }}}}.

You are a QA Test Engineer. Generate test cases for these requirements.

REQUIREMENTS:
{reqs_text}

INSTRUCTIONS:
Generate 2-4 test cases per requirement covering:
- Happy path (normal successful flow)
- Edge cases (boundary conditions, empty inputs, maximum limits)
- Error scenarios (invalid inputs, system failures)

Each test case must have:
- Unique test_id (TC-001, TC-002, etc.)
- Requirement ID it tests
- Test description
- Test steps (numbered, specific actions)
- Expected result (exact expected behavior)

OUTPUT FORMAT (JSON only):
{{{{
  "test_cases": [
    {{{{
      "test_id": "TC-001",
      "requirement_id": "REQ-001",
      "test_description": "Verify temperature recording occurs every 5 minutes",
      "test_steps": [
        "Power on weather station",
        "Wait for 5 minutes",
        "Check temperature log for new entry",
        "Wait another 5 minutes",
        "Verify second entry appears"
      ],
      "expected_result": "Temperature readings appear in log exactly 5 minutes apart with accurate timestamps"
    }},
    {{{{
      "test_id": "TC-002",
      "requirement_id": "REQ-001",
      "test_description": "Verify temperature recording continues after power interruption",
      "test_steps": [
        "Power on weather station",
        "Wait for 10 minutes (2 recordings)",
        "Disconnect power for 10 seconds",
        "Reconnect power",
        "Wait 5 minutes"
      ],
      "expected_result": "System resumes recording every 5 minutes after power restoration"
    }}}}
  ]
}}}}

RESPOND WITH JSON ONLY."""
