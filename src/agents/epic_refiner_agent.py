from .base_agent import BaseAgent
from typing import Dict, Any

class EpicRefinerAgent(BaseAgent):
    """Refines and merges epics - replaces refine_epics_v2 second pass"""

    def __init__(self):
        super().__init__(
            name="Epic Refiner",
            role="Epic Quality Specialist",
            goal="Refine and optimize epic structure"
        )

    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        raw_epics = context.get('raw_epics', [])
        requirements = context.get('requirements', [])

        epics_text = "\n".join([
            f"- {epic['epic_id']}: {epic['epic_name']} - {epic['epic_description']} (Requirements: {', '.join(epic['requirement_ids'])})"
            for epic in raw_epics
        ])

        reqs_text = "\n".join([
            f"- {req['id']}: {req['description']}"
            for req in requirements
        ])

        return f"""RESPOND WITH JSON ONLY. Do not include any prose, explanations, markdown headers, or text outside the JSON. Your entire response must be a single valid JSON object starting with {{{{ and ending with }}}}.

You are an Epic Quality Specialist performing second-pass epic optimization.

RAW EPICS (from first pass):
{epics_text}

ALL REQUIREMENTS (for reference):
{reqs_text}

REFINEMENT RULES (apply in order):
1. MERGE SIMILAR: If 2+ epics cover the same feature area or business capability, merge them
   - Example: "User Login" + "User Authentication" → "User Authentication & Authorization"
   - Keep the more comprehensive epic name
2. SPLIT BROAD: If an epic has >6 requirements or covers disparate concerns, split it
   - Example: "Data Management" with 8 requirements about collection, storage, transmission → split into "Data Collection" + "Data Storage" + "Data Transmission"
3. BALANCE SIZE: Target 2-5 requirements per epic (optimal: 3-4)
4. VERIFY COVERAGE: Ensure ALL requirements are assigned to exactly one epic
5. RENUMBER: Renumber epics sequentially (EPIC-001, EPIC-002, ...) after merging/splitting
6. IMPROVE NAMES: Make epic names more specific and business-focused

MERGE CRITERIA (merge if ALL true):
- Epics share >50% of the same functional area
- Combined epic would have ≤6 requirements
- Names are synonyms (e.g., "Login" and "Authentication", "Store" and "Persistence")

SPLIT CRITERIA (split if ANY true):
- Epic has >6 requirements
- Requirements cover 2+ distinct workflows (e.g., read vs write, input vs output)
- Requirements span different system components
- Requirements serve different user personas

OUTPUT FORMAT (JSON only):
{{{{
  "epics": [
    {{{{
      "epic_id": "EPIC-001",
      "epic_name": "Environmental Data Collection",
      "epic_description": "Automated collection of temperature, humidity, and pressure readings from weather sensors",
      "requirement_ids": ["REQ-001", "REQ-002", "REQ-003"]
    }}}},
    {{{{
      "epic_id": "EPIC-002",
      "epic_name": "Data Transmission & Synchronization",
      "epic_description": "Reliable transmission of sensor data to remote servers with retry and error handling",
      "requirement_ids": ["REQ-004", "REQ-005"]
    }}}}
  ]
}}}}

CRITICAL RULES:
1. Renumber epics after merge/split: EPIC-001, EPIC-002, EPIC-003, ...
2. Each epic: 2-5 requirements (avoid 1 or >6)
3. No duplicate requirement assignments
4. All requirements must be covered
5. Epic names: specific, business-focused, Title Case
6. Epic descriptions: updated to reflect merged/split scope

MERGE EXAMPLE:
Before:
- EPIC-001: "User Login" (REQ-001, REQ-002)
- EPIC-002: "User Authentication" (REQ-003)
After:
- EPIC-001: "User Authentication & Authorization" (REQ-001, REQ-002, REQ-003)

SPLIT EXAMPLE:
Before:
- EPIC-001: "Data Management" (REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007)
After:
- EPIC-001: "Data Collection" (REQ-001, REQ-002, REQ-003)
- EPIC-002: "Data Storage" (REQ-004, REQ-005)
- EPIC-003: "Data Transmission" (REQ-006, REQ-007)

BAD EXAMPLES (what NOT to do):
❌ Epic with 1 requirement — too small, should merge
❌ Epic with 8 requirements — too large, should split
❌ Duplicate assignment: REQ-005 in both EPIC-001 and EPIC-002
❌ Missing requirement: REQ-010 not assigned to any epic

GOOD EXAMPLES (correct format):
✅ Balanced: 3-4 requirements per epic
✅ Clear names: "Patient Demographics Management", "Alert Notification System"
✅ Specific descriptions: "Capture, validate, and maintain patient demographic data including name, address, age, and emergency contacts"
✅ Complete coverage: all requirements assigned exactly once

RESPOND WITH JSON ONLY."""
