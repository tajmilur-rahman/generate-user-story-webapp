from .base_agent import BaseAgent
from typing import Dict, Any

class StoryAgent(BaseAgent):
    """Generates user stories with acceptance criteria - replaces story generation in convert_to_user_stories"""

    def __init__(self):
        super().__init__(
            name="Story Writer",
            role="User Story Specialist",
            goal="Write clear, testable user stories following INVEST principles",
            temperature=0.4  # Slightly higher for creative story writing
        )

    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        requirements_batch = context.get('requirements_batch', [])
        epic = context.get('epic', {})

        reqs_text = "\n".join([
            f"- {req['id']}: {req['description']}"
            for req in requirements_batch
        ])

        return f"""RESPOND WITH JSON ONLY. Do not include any prose, explanations, markdown headers, or text outside the JSON. Your entire response must be a single valid JSON object starting with {{{{ and ending with }}}}.

You are a User Story Specialist. Write user stories for these requirements.

EPIC CONTEXT:
{epic.get('epic_name', 'N/A')}: {epic.get('epic_description', 'N/A')}

REQUIREMENTS TO CONVERT:
{reqs_text}

INSTRUCTIONS:
1. Write one user story per requirement
2. Format: "As a [user type], I want to [action] so that [benefit]"
3. Add 3-5 acceptance criteria per story (Given-When-Then format)
4. Add Definition of Done (unit tests, code review, integration testing)
5. Estimate story points (1, 2, 3, 5, 8)
6. Follow INVEST principles (Independent, Negotiable, Valuable, Estimable, Small, Testable)

OUTPUT FORMAT (JSON only):
{{{{
  "stories": [
    {{{{
      "story_id": "STORY-001",
      "requirement_id": "REQ-001",
      "user_story": "As a weather station operator, I want the system to automatically record temperature every 5 minutes so that I have continuous monitoring data",
      "acceptance_criteria": [
        "Given the station is powered on, When 5 minutes elapse, Then a new temperature reading is recorded",
        "Given temperature is recorded, When storage is checked, Then the reading includes timestamp and value",
        "Given readings are being recorded, When I check the log, Then I see entries exactly 5 minutes apart"
      ],
      "definition_of_done": [
        "Unit tests written with >80% coverage",
        "Code reviewed and approved",
        "Integration tested with real sensor",
        "Performance verified (sub-second recording time)"
      ],
      "story_points": 3,
      "priority": "HIGH"
    }}}}
  ]
}}}}

RESPOND WITH JSON ONLY."""
