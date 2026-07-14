from .base_agent import BaseAgent
from typing import Dict, Any

class RewriterAgent(BaseAgent):
    """Improves low-quality stories based on reviewer feedback"""

    def __init__(self):
        super().__init__(
            name="Story Rewriter",
            role="Story Improvement Specialist",
            goal="Fix low-quality stories to achieve INVEST score ≥70",
            temperature=0.5  # Higher for creative rewriting
        )

    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        story = context.get('story', {})
        review = context.get('review', {})

        return f"""RESPOND WITH JSON ONLY. Do not include any prose, explanations, markdown headers, or text outside the JSON. Your entire response must be a single valid JSON object starting with {{{{ and ending with }}}}.

You are a Story Improvement Specialist. Rewrite this low-quality story to address ALL identified issues and achieve INVEST score ≥70.

ORIGINAL STORY (Score: {review.get('total_score', 0)}/100):
Story ID: {story.get('story_id', 'N/A')}
Requirement ID: {story.get('requirement_id', 'N/A')}
User Story: {story.get('user_story', 'N/A')}
Acceptance Criteria: {story.get('acceptance_criteria', [])}
Definition of Done: {story.get('definition_of_done', [])}
Story Points: {story.get('story_points', 'N/A')}

INVEST SCORES (current):
{review.get('invest_scores', {{}})}

ISSUES IDENTIFIED (must fix ALL):
{review.get('issues', [])}

REVIEWER FEEDBACK:
{review.get('feedback', 'N/A')}

REWRITING RULES (apply to fix issues):
1. PRESERVE INTENT: Keep the original requirement purpose and scope
2. ADD [SPECIFIC ELEMENTS]: If missing, insert "[specific elements: field1, field2, ...]" clause with actual component/field names from the requirement
3. ADD/FIX "SO THAT": If missing or vague, add concrete benefit clause describing measurable outcome
4. SPECIFIC USER TYPE: Replace "As a user" with specific role (e.g., "As a data analyst", "As a system administrator")
5. ADD ACCEPTANCE CRITERIA: If <3 criteria, add more. Make them Given-When-Then format with actual field names
6. MAKE TESTABLE: Use concrete field names, values, and measurable outcomes in acceptance criteria
7. REDUCE SCOPE: If story points >5, narrow the scope to make it completable in one sprint
8. REMOVE VAGUENESS: Replace vague terms ("good", "fast", "flexible") with specific, measurable requirements
9. REMOVE DEPENDENCIES: Eliminate "depends on", "requires", "after completing" references
10. SPECIFIC DOD: Make Definition of Done items concrete and measurable

USER STORY FORMAT (MANDATORY):
As a [specific role], I want to [specific action] using [specific elements: field1, field2, sensor3], so that [concrete, measurable benefit].

ACCEPTANCE CRITERIA FORMAT:
- Given [specific context with field names], When [specific action], Then [specific outcome with expected values]
- Include at least one error/edge case scenario
- 3-5 criteria total

OUTPUT FORMAT (JSON only):
{{{{
  "rewritten_story": {{{{
    "story_id": "{story.get('story_id', 'N/A')}",
    "requirement_id": "{story.get('requirement_id', 'N/A')}",
    "epic_id": "{story.get('epic_id', 'N/A')}",
    "epic_name": "{story.get('epic_name', 'N/A')}",
    "user_story": "As a weather station operator, I want the system to automatically record temperature readings using [specific elements: thermometer sensor, timestamp, temperature_value in Celsius], so that I have continuous environmental monitoring data for detecting anomalies within 5 minutes",
    "acceptance_criteria": [
      "Given the weather station is powered on, When 5 minutes elapse, Then a new temperature reading is recorded in the readings table with sensor_id, timestamp, and temperature_value fields",
      "Given temperature is recorded, When I query the readings table, Then the record includes all 3 fields (sensor_id, timestamp, temperature_value) and timestamp is in UTC format",
      "Given readings are being recorded, When I check the log for the past hour, Then I see exactly 12 entries spaced 5 minutes apart",
      "Given the thermometer sensor is disconnected, When the 5-minute interval elapses, Then an error is logged with message 'Sensor disconnected' and no reading is recorded",
      "Given temperature exceeds range (-50 to 50 Celsius), When reading is recorded, Then quality_flag is set to 'out_of_range'"
    ],
    "definition_of_done": [
      "Unit tests written for temperature_reader.record() covering normal path, sensor disconnection, and out-of-range scenarios",
      "Integration test with real thermometer sensor validates 5-minute interval timing accuracy",
      "Code review completed and approved by technical lead",
      "Performance test confirms recording completes in <500ms per reading",
      "Error handling tested for all identified failure scenarios",
      "Deployment tested in staging environment with live sensor data"
    ],
    "story_points": 3,
    "priority": "{story.get('priority', 'MEDIUM')}"
  }}}},
  "changes_made": [
    "Added [specific elements: thermometer sensor, timestamp, temperature_value in Celsius] clause listing actual components",
    "Enhanced 'so that' clause from generic 'data available' to 'continuous monitoring for detecting anomalies within 5 minutes'",
    "Changed user type from generic 'user' to specific 'weather station operator'",
    "Increased acceptance criteria from 1 to 5, all using Given-When-Then format with actual field names",
    "Made all acceptance criteria testable and measurable with concrete expected outcomes",
    "Added error/edge case scenarios (sensor disconnection, out-of-range values)",
    "Made Definition of Done items specific with measurable outcomes",
    "Reduced story points from 8 to 3 by focusing scope on core recording functionality"
  ]
}}}}

CRITICAL RULES:
1. Fix ALL issues listed in the review feedback
2. MUST include [specific elements: ...] clause if it was flagged as missing
3. MUST add/improve "so that" clause if flagged
4. MUST add/improve acceptance criteria to 3-5 items if flagged
5. Use actual field names, sensors, components from the requirement
6. Make every criterion testable and measurable
7. Keep changes minimal - only fix what's needed to achieve ≥70 score
8. Preserve epic_id, epic_name, story_id, requirement_id, and priority

RESPOND WITH JSON ONLY."""
