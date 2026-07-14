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
        document = context.get('document', '')

        return f"""RESPOND WITH JSON ONLY. Do not include any prose, explanations, markdown headers, or text outside the JSON. Your entire response must be a single valid JSON object starting with {{{{ and ending with }}}}.

You are a senior software engineer extracting ALL functional requirements from a product specification document.

DOCUMENT TEXT:
{document}

EXTRACTION RULES (apply in order):
1. EXTRACT: Extract EVERY distinct functional requirement mentioned — do not skip, merge, or summarise.
2. PRECISE VERBS: Each requirement must use a precise verb (collect, calculate, transmit, validate, store, monitor, display, alert, authenticate, encrypt).
3. COMPREHENSIVE COVERAGE: Cover ALL functional areas:
   - Data acquisition, processing/calculation, storage, transmission
   - User interface, error handling, safety/security
   - Configuration, alerts/notifications, reporting
4. NO META-REQUIREMENTS: Do NOT include requirements about testing, documentation, or project management.
5. SPLIT BUNDLED REQUIREMENTS: If a sentence describes two distinct capabilities, split it into two requirements.
6. AIM FOR COMPLETENESS: Better to have too many specific requirements than too few.

REFINEMENT RULES (apply after extraction):
1. SPLIT: If any single requirement bundles two or more distinct capabilities, split it into separate requirements. Err on the side of splitting.
2. CLARIFY: Rewrite vague verbs ("handle", "support", "manage", "provide") to precise ones ("store", "validate", "transmit", "calculate", "alert", "display", "authenticate").
3. ADD IMPLIED: Insert clearly implied requirements that are missing (e.g., if data is transmitted it must first be aggregated; if a user logs in there must be a way to log out).
4. REMOVE DUPLICATES: Delete ONLY exact duplicate requirements. Do NOT merge requirements that cover different functional areas — keep them separate.
5. PRESERVE GRANULARITY: Keep the total number of requirements high. It is better to have 15 specific requirements than 5 merged ones.

OUTPUT FORMAT (JSON only):
{{{{
  "requirements": [
    {{{{
      "id": "REQ-001",
      "description": "Record temperature readings automatically every 5 minutes"
    }}}},
    {{{{
      "id": "REQ-002",
      "description": "Store temperature data persistently with timestamp"
    }}}}
  ]
}}}}

CRITICAL RULES:
1. Each requirement: ONE sentence starting with a precise action verb
2. NO vague verbs: "handle", "manage", "support", "provide"
3. NO meta-requirements: testing, documentation, quality assurance
4. Number sequentially: REQ-001, REQ-002, REQ-003, ...
5. Preserve granularity: split rather than merge

BAD EXAMPLES (what NOT to do):
❌ "The system shall provide good user experience" — too vague, no specific action
❌ "The system shall handle data" — vague verb "handle"
❌ "The system shall support testing and documentation" — meta-requirement
❌ "The system shall collect, process, and transmit sensor data" — bundled, should be 3 requirements

GOOD EXAMPLES (correct format):
✅ "Record temperature readings automatically every 5 minutes"
✅ "Store temperature data persistently with timestamp and sensor ID"
✅ "Validate user credentials against stored password hash"
✅ "Transmit compressed data packets when satellite uplink is available"

RESPOND WITH JSON ONLY."""
