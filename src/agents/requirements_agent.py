from .base_agent import BaseAgent
from typing import Dict, Any

class RequirementsAgent(BaseAgent):
    """Extracts and refines requirements - replaces extract_list + refine_requirements"""

    def __init__(self):
        super().__init__(
            name="Requirements Extractor",
            role="Requirements Analyst",
            goal="Extract and refine all requirements from documents"
        )

    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        return """RESPOND WITH JSON ONLY. Do not include any prose, explanations, markdown headers, or text outside the JSON. Your entire response must be a single valid JSON object starting with {{ and ending with }}.

You are a Requirements Analyst. Extract and refine all requirements from the document.

INSTRUCTIONS:
1. Extract EVERY requirement (functional and non-functional)
2. Merge duplicate or overlapping requirements
3. Split overly broad requirements into specific ones
4. Remove meta-requirements (e.g., "system should have good documentation")
5. Number requirements sequentially starting from REQ-001
6. Aim for 10-20 clear, specific requirements

OUTPUT FORMAT (JSON only):
{{
  "requirements": [
    {{
      "id": "REQ-001",
      "description": "The system shall record temperature every 5 minutes",
      "type": "functional",
      "priority": "high"
    }},
    {{
      "id": "REQ-002",
      "description": "The system shall achieve 99.9% uptime",
      "type": "non-functional",
      "priority": "medium"
    }}
  ]
}}

RESPOND WITH JSON ONLY. No markdown, no prose."""
