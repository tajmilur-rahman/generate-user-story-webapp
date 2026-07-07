from .base_agent import BaseAgent
from typing import Dict, Any, List

class ReviewerAgent(BaseAgent):
    """Reviews and scores user stories on INVEST criteria"""

    def __init__(self):
        super().__init__(
            name="Story Reviewer",
            role="Quality Assurance Reviewer",
            goal="Score every story on INVEST criteria and identify issues"
        )

    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        stories = context.get('stories', [])

        stories_text = self._format_stories(stories)

        return f"""RESPOND WITH JSON ONLY. Do not include any prose, explanations, markdown headers, or text outside the JSON. Your entire response must be a single valid JSON object starting with {{{{ and ending with }}}}.

You are a Story Quality Reviewer. Score each story on INVEST criteria.

STORIES TO REVIEW:
{stories_text}

INVEST CRITERIA (score each 0-10):
- **Independent**: Can be developed without dependencies (check for "depends on", "requires")
- **Negotiable**: Implementation details flexible (avoid "must use", "exactly")
- **Valuable**: Clear user benefit (look for "so that" clause)
- **Estimable**: Team can estimate effort (not vague like "good performance")
- **Small**: Fits in one sprint (story points ≤5 ideal)
- **Testable**: Has concrete acceptance criteria

SCORING:
- 90-100: Excellent story, ready to implement
- 70-89: Good story, minor improvements possible
- 50-69: Needs improvement, rewrite recommended
- 0-49: Poor quality, must rewrite

OUTPUT FORMAT (JSON only):
{{{{
  "story_reviews": [
    {{{{
      "story_id": "STORY-001",
      "invest_scores": {{{{
        "independent": 10,
        "negotiable": 8,
        "valuable": 10,
        "estimable": 7,
        "small": 9,
        "testable": 10
      }}}},
      "total_score": 90,
      "issues": [],
      "feedback": "Excellent story with clear value and testable criteria",
      "recommendation": "APPROVE"
    }}}},
    {{{{
      "story_id": "STORY-002",
      "invest_scores": {{{{
        "independent": 9,
        "negotiable": 7,
        "valuable": 4,
        "estimable": 6,
        "small": 8,
        "testable": 3
      }}}},
      "total_score": 62,
      "issues": [
        "Missing 'so that' clause - unclear user value",
        "No acceptance criteria - not testable"
      ],
      "feedback": "Story lacks clear benefit and testable criteria. Add 'so that' clause and 3+ acceptance criteria.",
      "recommendation": "REWRITE"
    }}}}
  ],
  "summary": {{{{
    "total_stories": 2,
    "average_score": 76,
    "stories_below_threshold": 1,
    "stories_needing_rewrite": ["STORY-002"]
  }}}}
}}}}

RESPOND WITH JSON ONLY."""

    def _format_stories(self, stories: List[Dict]) -> str:
        formatted = []
        for story in stories:
            formatted.append(f"""
Story ID: {story.get('story_id', 'N/A')}
User Story: {story.get('user_story', 'N/A')}
Acceptance Criteria: {story.get('acceptance_criteria', [])}
Story Points: {story.get('story_points', 'N/A')}
""")
        return "\n---\n".join(formatted)
