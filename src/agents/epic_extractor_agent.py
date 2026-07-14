from .base_agent import BaseAgent
from typing import Dict, Any

class EpicExtractorAgent(BaseAgent):
    """Extracts initial epics from requirements - replaces extract_epics_v2 first pass"""

    def __init__(self):
        super().__init__(
            name="Epic Extractor",
            role="Epic Strategist",
            goal="Extract 5-10 strategic epics from requirements"
        )

    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        requirements = context.get('requirements', [])

        reqs_text = "\n".join([
            f"- {req['id']}: {req['description']}"
            for req in requirements
        ])

        return f"""RESPOND WITH JSON ONLY. Do not include any prose, explanations, markdown headers, or text outside the JSON. Your entire response must be a single valid JSON object starting with {{{{ and ending with }}}}.

You are an Epic Strategist grouping requirements into logical feature areas (epics).

REQUIREMENTS TO GROUP:
{reqs_text}

GROUPING RULES:
1. CREATE 5-10 EPICS: Aim for 5-10 epics total (optimal: 6-8)
2. GROUP BY FEATURE AREA: Group 2-5 related requirements per epic based on:
   - Functional similarity (all about data collection, all about user management, etc.)
   - Shared user workflows
   - Common system components
   - Related business capabilities
3. EPIC NAMES: Clear, business-focused names in Title Case
   - ✅ GOOD: "Environmental Data Collection", "User Authentication", "Alert Management"
   - ❌ BAD: "Feature 1", "Requirements Group", "System Functions"
4. EPIC DESCRIPTIONS: 10-20 words describing the business value or capability
5. COMPLETE COVERAGE: Every requirement must belong to exactly one epic
6. BALANCED SIZE: Avoid epics with 1 requirement or >6 requirements

OUTPUT FORMAT (JSON only):
{{{{
  "epics": [
    {{{{
      "epic_id": "EPIC-001",
      "epic_name": "Environmental Data Collection",
      "epic_description": "Automated collection and recording of temperature, humidity, and pressure sensor readings",
      "requirement_ids": ["REQ-001", "REQ-002", "REQ-003"]
    }}}},
    {{{{
      "epic_id": "EPIC-002",
      "epic_name": "Data Transmission",
      "epic_description": "Reliable transmission of collected data to remote servers via satellite uplink",
      "requirement_ids": ["REQ-004", "REQ-005"]
    }}}}
  ]
}}}}

CRITICAL RULES:
1. Number epics sequentially: EPIC-001, EPIC-002, EPIC-003, ...
2. Each epic: 2-5 requirements (optimal: 3-4)
3. Epic names: Title Case, business-focused, no technical jargon
4. Epic descriptions: specific capabilities, not vague statements
5. NO orphaned requirements: every requirement must be assigned
6. NO duplicate assignments: each requirement appears in exactly one epic

BAD EXAMPLES (what NOT to do):
❌ "epic_name": "System Requirements" — too vague
❌ "epic_name": "Feature Set A" — meaningless
❌ "epic_description": "Various system functions" — not specific
❌ "requirement_ids": ["REQ-001", "REQ-002", "REQ-003", "REQ-004", "REQ-005", "REQ-006", "REQ-007"] — too many (7 requirements)

GOOD EXAMPLES (correct format):
✅ "epic_name": "Patient Demographics Management"
✅ "epic_description": "Capture and maintain patient demographic data including name, address, age, and emergency contacts"
✅ "requirement_ids": ["REQ-001", "REQ-002", "REQ-003"] — balanced (3 requirements)

RESPOND WITH JSON ONLY."""
