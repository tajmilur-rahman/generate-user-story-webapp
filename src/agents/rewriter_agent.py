from .base_agent import BaseAgent
from .schemas import RewriteOutput
from .settings import include_estimates
from typing import Dict, Any

class RewriterAgent(BaseAgent):
    """Improves low-quality stories based on reviewer feedback"""

    def __init__(self):
        super().__init__(
            name="Story Rewriter",
            role="Story Improvement Specialist",
            goal="Repair the listed defects in a story without changing anything else",
            # Zero on purpose. This is a repair, not composition: the task is to
            # reproduce the original with specific defects corrected, so there is
            # nothing here that benefits from sampling. Variance shows up only as
            # drift away from the original subject -- a run at 0.5 returned a
            # story the judge had scored 94 as one it scored 64. Greedy decoding
            # also makes a repair reproducible, so the same defect and the same
            # story yield the same correction every time.
            temperature=0.0,
            output_model=RewriteOutput
        )

    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        story = context.get('story', {})
        review = context.get('review', {})

        # Resolved outside the f-string on purpose. Written inline as
        # `review.get('invest_scores', {{}})` the default is parsed as a set
        # literal containing an empty dict, which is unhashable, so building
        # this prompt raised TypeError on every call and the rewrite path could
        # never run.
        invest_scores = review.get('invest_scores', {})
        issues = review.get('issues', [])

        # Mirrors the Story Writer: estimates are only mentioned when enabled,
        # so a rewrite does not reintroduce fields generation left out.
        if include_estimates():
            estimate_summary = f"\nStory Points: {story.get('story_points', 'N/A')}"
            estimate_fields = (
                ',\n    "story_points": 3,\n    "priority": "'
                + str(story.get('priority', 'MEDIUM')) + '"')
            estimate_preserve = ", and priority"
        else:
            estimate_summary = ""
            estimate_fields = ""
            estimate_preserve = ""

        return f"""RESPOND WITH JSON ONLY. Do not include any prose, explanations, markdown headers, or text outside the JSON. Your entire response must be a single valid JSON object starting with {{{{ and ending with }}}}.

You are a Story Improvement Specialist. Repair the specific defects listed
below in the story provided, so it reaches an INVEST score of 70 or more.

ORIGINAL STORY (Score: {review.get('total_score', 0)}/100):
Story ID: {story.get('story_id', 'N/A')}
Requirement ID: {story.get('requirement_id', 'N/A')}
User Story: {story.get('user_story', 'N/A')}
Acceptance Criteria: {story.get('acceptance_criteria', [])}
Deliverables: {story.get('deliverables', {}) or story.get('definition_of_done', [])}{estimate_summary}

INVEST SCORES (current):
{invest_scores}

ISSUES IDENTIFIED (must fix ALL):
{issues}

REVIEWER FEEDBACK:
{review.get('feedback', 'N/A')}

THIS IS A REPAIR, NOT A REWRITE.

The story above is mostly correct. Your job is to fix the specific defects
listed under ISSUES IDENTIFIED and change nothing else. A story that comes back
altered beyond those defects is a worse answer than one left alone, even if the
new version reads well on its own.

BEFORE ANYTHING ELSE:
1. REPAIR ONLY WHAT IS LISTED: every issue above must be fixed, and nothing that
   is not listed may be changed. If a sentence has no listed defect, reproduce
   it exactly.
2. PRESERVE THE SUBJECT: the repaired story must be about the same actor, the
   same capability and the same components as the original. Never substitute a
   different role, sensor, field, module or capability.
3. PRESERVE THE SCOPE: do not widen the story to cover more, and do not narrow
   it to cover less. Keep the same number of acceptance criteria unless a listed
   issue says there are too few.

HOW TO FIX EACH KIND OF DEFECT:
4. MISSING [SPECIFIC ELEMENTS]: insert "[specific elements: field1, field2, ...]"
   naming components already referenced by the original story or its requirement
5. MISSING OR VAGUE "SO THAT": state the concrete benefit the original implies
6. GENERIC ACTOR: replace "As a user" with the specific role the original is
   about -- do not invent a new one
7. TOO FEW ACCEPTANCE CRITERIA: add only enough to reach three, in
   Given-When-Then form, covering behaviour the original already describes
8. UNTESTABLE CRITERIA: restate them with the concrete field names and values
   already present, without adding new behaviour
9. VAGUE TERMS: replace "good", "fast", "flexible" with what the original means
10. DEPENDENCIES: remove "depends on", "requires", "after completing" phrasing

USER STORY FORMAT (MANDATORY):
As a [specific role], I want to [specific action] using [specific elements: field1, field2, sensor3], so that [concrete, measurable benefit].

ACCEPTANCE CRITERIA FORMAT:
- Given [specific context with field names], When [specific action], Then [specific outcome with expected values]
- Keep the criteria the original already has. Add one only when a listed issue
  says there are too few, and stop at three.

OUTPUT FORMAT (JSON only):
{{{{
  "rewritten_story": {{{{
    "story_id": "{story.get('story_id', 'N/A')}",
    "requirement_id": "{story.get('requirement_id', 'N/A')}",
    "epic_id": "{story.get('epic_id', 'N/A')}",
    "epic_name": "{story.get('epic_name', 'N/A')}",
    "user_story": "As a <the original role>, I want to <the original action> using [specific elements: <components already named above>], so that <the benefit the original implies>",
    "acceptance_criteria": [
      "Given <context using the original's own field names>, When <the original's action>, Then <the outcome the original states>",
      "Given <an error condition the original already mentions>, When <it occurs>, Then <the behaviour the original states>"
    ],
    "deliverables": {{{{
      "<categories carried over from the original>": [
        "<items carried over, edited only where a listed issue requires it>"
      ]
    }}}}{estimate_fields}
  }}}},
  "changes_made": [
    "<one line per listed issue, naming the issue and what you changed to fix it>"
  ]
}}}}

The angle brackets above mark placeholders describing WHERE content goes. Fill
every one from the ORIGINAL STORY at the top of this prompt. Do not copy the
placeholder text, and do not invent subject matter that is not already in the
original story or its requirement.

CRITICAL RULES:
1. Change ONLY what the listed issues require. Anything not listed comes through
   unchanged, word for word
2. The subject stays the same: same actor, same capability, same components. A
   repaired story about something else is a failed repair
3. Fix EVERY listed issue -- a partial repair will be sent back
4. Use only field names, components and behaviour already present in the
   original story or its requirement. Invent nothing
5. Make every criterion testable, using the original's own values
6. Preserve epic_id, epic_name, story_id and requirement_id{estimate_preserve}
7. If an issue cannot be fixed without inventing content, leave that part as it
   is and say so in changes_made

RESPOND WITH JSON ONLY."""
