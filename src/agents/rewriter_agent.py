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

You are a Story Improvement Specialist. Rewrite this low-quality story to address all issues.

ORIGINAL STORY (Score: {review.get('total_score', 0)}/100):
{story.get('user_story', 'N/A')}

INVEST SCORES:
{review.get('invest_scores', {{}})}

ISSUES IDENTIFIED:
{review.get('issues', [])}

FEEDBACK:
{review.get('feedback', 'N/A')}

INSTRUCTIONS:
1. Preserve the original intent and requirement
2. Add "so that [benefit]" clause if missing (improves Valuable score)
3. Make story smaller if >5 story points (improves Small score)
4. Add 3-5 concrete acceptance criteria (improves Testable score)
5. Remove vague terms like "good", "fast", "user-friendly" (improves Estimable score)
6. Remove dependencies on other stories (improves Independent score)

OUTPUT FORMAT (JSON only):
{{{{
  "rewritten_story": {{{{
    "story_id": "{story.get('story_id', 'N/A')}",
    "requirement_id": "{story.get('requirement_id', 'N/A')}",
    "user_story": "As a [specific user type], I want to [specific action] so that [concrete benefit]",
    "acceptance_criteria": [
      "Given [context], When [action], Then [expected result with metrics]",
      "Given [context], When [action], Then [expected result with metrics]",
      "Given [context], When [action], Then [expected result with metrics]"
    ],
    "definition_of_done": [
      "Unit tests written with >80% coverage",
      "Code reviewed and approved",
      "Integration tested in staging environment"
    ],
    "story_points": 3,
    "priority": "{story.get('priority', 'MEDIUM')}"
  }}}},
  "changes_made": [
    "Added 'so that' clause to clarify user benefit",
    "Added 3 specific acceptance criteria with measurable outcomes",
    "Reduced story points from 8 to 3 by narrowing scope"
  ]
}}}}

RESPOND WITH JSON ONLY."""
