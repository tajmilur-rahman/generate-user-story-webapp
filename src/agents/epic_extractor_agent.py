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

You are an Epic Strategist. Extract initial epics from these requirements.

REQUIREMENTS:
{reqs_text}

INSTRUCTIONS:
1. Create 5-10 epics (aim for 7-10)
2. Each epic should group 2-5 related requirements
3. Epic names should be clear and business-focused (e.g., "User Authentication", "Data Management")
4. Every requirement must belong to at least one epic
5. Focus on logical grouping by feature area

OUTPUT FORMAT (JSON only):
{{{{
  "epics": [
    {{{{
      "epic_id": "EPIC-001",
      "epic_name": "Temperature Monitoring",
      "epic_description": "Core temperature sensing and recording capabilities",
      "requirement_ids": ["REQ-001", "REQ-002"]
    }}}}
  ]
}}}}

RESPOND WITH JSON ONLY."""
