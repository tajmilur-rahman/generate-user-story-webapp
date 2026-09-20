"""
Deterministic INVEST checks.

The quality gate used to be a single LLM call scoring every story, where the
judge was the same model family that wrote them. It returned 93/100 on two
consecutive runs over different extractions and never once scored a story below
the rewrite threshold, so the rewrite path was dead code in practice -- which is
how a story-ID corruption bug stayed latent for so long.

Much of INVEST is mechanically checkable. Running those checks first is free,
unbiased, and cannot return a false pass, and it leaves the model to judge only
what a rule genuinely cannot decide.

Each check returns (passed, issue). A story's deterministic score is the
weighted proportion of checks it passes.
"""

import re
from typing import Any, Dict, List, Tuple

# "As a <role>, I want <action>, so that <benefit>"
_STORY_FORM_RE = re.compile(
    r"as\s+an?\s+.+?,\s*i\s+want\s+.+?,\s*so\s+that\s+.+",
    re.IGNORECASE | re.DOTALL,
)

# A story that reads as several stories joined together is not Small.
_CONJUNCTION_RE = re.compile(r"\b(?:and also|as well as|in addition)\b", re.IGNORECASE)

# Criteria that assert nothing checkable.
_VAGUE_CRITERIA = {
    "works", "works correctly", "works as expected", "is correct", "done",
    "complete", "completed", "functions properly", "no errors", "tbd", "n/a",
}

# Weights sum to 100, and are set so a single critical failure crosses the
# rewrite threshold of 70: a story in the wrong form scores 65, and one with no
# acceptance criteria scores 60 (it also fails the specificity check). Softer signals -- a vague
# criterion, a missing requirement link -- flag without forcing a rewrite on
# their own, and accumulate if a story has several.
_WEIGHTS = {
    "story_form": 35,
    "has_acceptance_criteria": 25,
    "criteria_are_specific": 15,
    "has_definition_of_done": 10,
    "traces_to_requirement": 5,
    "is_small": 10,
}

# Word count above which a story is unlikely to be Small. Deliberately generous:
# this should flag runaway stories, not police verbosity.
_MAX_STORY_WORDS = 80


def _story_text(story: Dict[str, Any]) -> str:
    return str(story.get("user_story", "") or "").strip()


def _criteria(story: Dict[str, Any]) -> List[str]:
    raw = story.get("acceptance_criteria", []) or []
    if isinstance(raw, str):
        raw = [raw]
    return [str(c).strip() for c in raw if str(c).strip()]


def check_story_form(story: Dict[str, Any]) -> Tuple[bool, str]:
    """Story follows the As-a / I-want / So-that form."""
    text = _story_text(story)
    if not text:
        return False, "Story text is empty"
    if not _STORY_FORM_RE.search(text):
        return False, (
            "Story does not follow 'As a <role>, I want <action>, so that "
            "<benefit>' form"
        )
    return True, ""


def check_has_acceptance_criteria(story: Dict[str, Any]) -> Tuple[bool, str]:
    """Testable: a story with no acceptance criteria cannot be verified."""
    if not _criteria(story):
        return False, "No acceptance criteria"
    return True, ""


def check_criteria_are_specific(story: Dict[str, Any]) -> Tuple[bool, str]:
    """Criteria that assert nothing are not testable."""
    criteria = _criteria(story)
    if not criteria:
        return False, "No acceptance criteria to assess"

    vague = [c for c in criteria if c.lower().rstrip(".") in _VAGUE_CRITERIA]
    if vague:
        return False, f"Vague acceptance criteria: {'; '.join(vague[:3])}"
    return True, ""


def check_has_definition_of_done(story: Dict[str, Any]) -> Tuple[bool, str]:
    dod = story.get("definition_of_done", []) or []
    if isinstance(dod, str):
        dod = [dod] if dod.strip() else []
    if not [d for d in dod if str(d).strip()]:
        return False, "No definition of done"
    return True, ""


def check_traces_to_requirement(story: Dict[str, Any]) -> Tuple[bool, str]:
    """Independent: a story should trace to the requirement it implements."""
    if not str(story.get("requirement_id", "") or "").strip():
        return False, "Story does not reference a requirement"
    return True, ""


def check_is_small(story: Dict[str, Any]) -> Tuple[bool, str]:
    """Small: flag stories that bundle several pieces of work."""
    text = _story_text(story)
    if not text:
        return False, "Story text is empty"

    words = len(text.split())
    if words > _MAX_STORY_WORDS:
        return False, f"Story is {words} words; likely covers several stories"

    if _CONJUNCTION_RE.search(text):
        return False, "Story joins multiple deliverables with a conjunction"
    return True, ""


CHECKS = {
    "story_form": check_story_form,
    "has_acceptance_criteria": check_has_acceptance_criteria,
    "criteria_are_specific": check_criteria_are_specific,
    "has_definition_of_done": check_has_definition_of_done,
    "traces_to_requirement": check_traces_to_requirement,
    "is_small": check_is_small,
}


def evaluate_story(story: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run every deterministic check against one story.

    Args:
        story: Story dictionary

    Returns:
        {"score": 0-100, "issues": [...], "passed": {...}}
    """
    issues: List[str] = []
    passed: Dict[str, bool] = {}
    score = 0

    for name, check in CHECKS.items():
        ok, issue = check(story)
        passed[name] = ok
        if ok:
            score += _WEIGHTS[name]
        elif issue:
            issues.append(issue)

    return {"score": score, "issues": issues, "passed": passed}


def evaluate_stories(stories: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Evaluate a batch, keyed by story id.

    Stories without an id fall back to their index, so a missing id never
    collapses two stories onto one result.
    """
    results = {}
    for idx, story in enumerate(stories):
        key = story.get("story_id") or f"index-{idx}"
        results[key] = evaluate_story(story)
    return results


def summarise_scores(scores: List[int]) -> Dict[str, Any]:
    """
    Describe a score distribution.

    A mean alone hides the failure this replaces: a judge returning the same
    number for every story looks identical to a genuinely uniform batch. Spread
    makes that visible.
    """
    if not scores:
        return {"count": 0, "mean": 0, "min": 0, "max": 0, "spread": 0,
                "distinct_values": 0}

    ordered = sorted(scores)
    mid = len(ordered) // 2
    median = (ordered[mid] if len(ordered) % 2
              else (ordered[mid - 1] + ordered[mid]) / 2)

    return {
        "count": len(ordered),
        "mean": round(sum(ordered) / len(ordered), 1),
        "median": median,
        "min": ordered[0],
        "max": ordered[-1],
        "spread": ordered[-1] - ordered[0],
        "distinct_values": len(set(ordered)),
    }
