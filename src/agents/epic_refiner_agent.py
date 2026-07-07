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

        return f"""RESPOND WITH JSON ONLY. Do not include any prose, explanations, markdown headers, or text outside the JSON. Your entire response must be a single valid JSON object starting with {{{{ and ending with }}}}.

You are an Epic Quality Specialist. Refine these raw epics.

RAW EPICS:
{epics_text}

INSTRUCTIONS:
1. Merge overly similar epics (if 2 epics cover same feature area)
2. Split overly broad epics (if epic covers too many disparate features)
3. Ensure epic names are clear and business-focused
4. Verify all requirements are covered
5. Aim for 5-10 final epics
6. Ensure no requirement appears in multiple epics

OUTPUT FORMAT (JSON only):
{{{{
  "epics": [
    {{{{
      "epic_id": "EPIC-001",
      "epic_name": "User Authentication & Authorization",
      "epic_description": "Complete user management including registration, login, and access control",
      "requirement_ids": ["REQ-001", "REQ-002", "REQ-005"],
      "priority": "HIGH"
    }}}}
  ]
}}}}

RESPOND WITH JSON ONLY."""
