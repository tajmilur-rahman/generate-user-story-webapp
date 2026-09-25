"""
Grounding checks for extracted requirements.

The Requirements Extractor invents subjects the source document never mentions.
In one run against a wilderness weather station specification it produced
requirements for humidity readings and light intensity control; neither word
occurs anywhere in the document, which covers temperature, pressure, sunshine,
rainfall and wind. Both fabrications carried full acceptance criteria,
deliverables and test cases downstream, arriving as credible as any grounded
story.

The agent prompt already forbids this explicitly, and the extractor runs at
temperature 0.0, so it is not sampling variance -- it is pattern completion
from the training distribution, and an instruction cannot verify itself.

This module checks the answer mechanically instead: a requirement that
introduces vocabulary absent from the source document is not grounded in it.
The check is deliberately conservative. Wrongly discarding a real requirement
is the failure mode already fixed twice in this pipeline, so the threshold is
set well below the weakest legitimate requirement observed, and everything
removed is reported rather than dropped silently.
"""

import os
import re
from typing import Any, Dict, List, Tuple

# Vocabulary that carries no grounding signal: it appears in requirements
# written about any system, so its presence in the source proves nothing.
_GENERIC_TERMS = {
    # structural / modal
    "the", "and", "for", "with", "from", "that", "this", "must", "shall",
    "will", "can", "should", "when", "then", "each", "every", "all", "any",
    "into", "over", "under", "within", "using", "via", "per", "its", "their",
    # generic system vocabulary
    "system", "systems", "data", "value", "values", "field", "fields",
    "record", "records", "recorded", "recording", "store", "stored",
    "storage", "storing", "collect", "collects", "collected", "collecting",
    "provide", "provides", "support", "supports", "enable", "enables",
    "generate", "generates", "process", "processes", "processing",
    "information", "report", "reports", "reporting", "status", "state",
    "interval", "intervals", "periodically", "automatically", "user",
    "users", "operator", "operators", "time", "times", "timestamp",
    "timestamps", "unit", "units", "type", "types", "number", "numbers",
    "module", "modules", "component", "components", "interface", "interfaces",
    "software", "hardware", "device", "devices", "instrument", "instruments",
    "measure", "measures", "measurement", "measurements", "reading",
    "readings", "monitor", "monitors", "monitoring", "send", "sends",
    "transmit", "transmits", "transmission", "request", "requests",
}

_WORD_RE = re.compile(r"[a-z][a-z0-9_]{2,}")

# Minimum fraction of a requirement's distinctive vocabulary that must occur in
# the source document.
#
# Measured against the wilderness weather station specification and the
# requirements one run produced from it, the two populations separate cleanly:
#
#     hallucinated   0% - 20%     (humidity, light intensity)
#     legitimate    33% - 100%
#
# 0.25 sits in that gap with five points of margin either side. A single
# borrowed word is not enough to ground a requirement -- the light intensity
# case scored 20% by reusing "remotely" while its actual subject was invented.
#
# This is tuned on one document, so it is deliberately set toward keeping
# requirements: wrongly discarding a real one is the failure already fixed
# twice here (7864d85, 3dbc2ba). Override with REQUIREMENT_GROUNDING_THRESHOLD.
_DEFAULT_THRESHOLD = 0.25


def _threshold() -> float:
    """Grounding threshold, overridable per deployment."""
    try:
        return float(os.getenv("REQUIREMENT_GROUNDING_THRESHOLD",
                               str(_DEFAULT_THRESHOLD)))
    except ValueError:
        return _DEFAULT_THRESHOLD


def _terms(text: str) -> List[str]:
    """Distinctive vocabulary of a piece of text, in order, without duplicates."""
    seen = []
    for word in _WORD_RE.findall((text or "").lower()):
        if word in _GENERIC_TERMS or word in seen:
            continue
        seen.append(word)
    return seen


def _source_vocabulary(source_text: str) -> set:
    """Every word form present in the source document.

    Matching is on stems rather than whole words so that a requirement saying
    "sensors" is grounded by a document saying "sensor".
    """
    words = set(_WORD_RE.findall((source_text or "").lower()))
    stems = set()
    for word in words:
        stems.add(word)
        for suffix in ("s", "es", "ed", "ing"):
            if word.endswith(suffix) and len(word) - len(suffix) >= 3:
                stems.add(word[: -len(suffix)])
    return stems


def _is_present(term: str, vocabulary: set) -> bool:
    """Whether a term occurs in the source, allowing simple morphology."""
    if term in vocabulary:
        return True
    for suffix in ("s", "es", "ed", "ing"):
        if term.endswith(suffix) and term[: -len(suffix)] in vocabulary:
            return True
    return any(term + suffix in vocabulary for suffix in ("s", "es", "ed", "ing"))


def check_requirement(requirement: Dict[str, Any],
                      source_text: str) -> Dict[str, Any]:
    """
    Assess whether one requirement is grounded in the source document.

    Args:
        requirement: Requirement dictionary with a description
        source_text: The document the requirements were extracted from

    Returns:
        {"grounded": bool, "matched": [...], "missing": [...]}
    """
    vocabulary = _source_vocabulary(source_text)
    terms = _terms(requirement.get("description", ""))

    matched = [t for t in terms if _is_present(t, vocabulary)]
    missing = [t for t in terms if t not in matched]

    # A requirement with no distinctive vocabulary at all says nothing specific
    # enough to be checked; treat it as grounded rather than invent a verdict.
    coverage = (len(matched) / len(terms)) if terms else 1.0
    grounded = coverage >= _threshold()

    return {"grounded": grounded, "coverage": round(coverage, 3),
            "matched": matched, "missing": missing}


def filter_grounded(requirements: List[Dict[str, Any]],
                    source_text: str) -> Tuple[List[Dict[str, Any]],
                                               List[Dict[str, Any]]]:
    """
    Split requirements into those grounded in the source and those not.

    Args:
        requirements: Extracted requirements
        source_text: The document they were extracted from

    Returns:
        (grounded, rejected) where each rejected entry carries the requirement
        plus the vocabulary that could not be found, so the caller can report
        what was removed rather than dropping it silently.
    """
    if not requirements or not source_text:
        return list(requirements or []), []

    grounded, rejected = [], []
    for requirement in requirements:
        if not isinstance(requirement, dict):
            continue
        outcome = check_requirement(requirement, source_text)
        if outcome["grounded"]:
            grounded.append(requirement)
        else:
            rejected.append({
                "id": requirement.get("id", ""),
                "description": requirement.get("description", ""),
                "missing_terms": outcome["missing"],
                "coverage": outcome["coverage"],
            })
    return grounded, rejected
