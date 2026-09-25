"""
Feature toggles for the agent pipeline.

Kept separate from the agents so a capability can be switched off without
deleting the code that implements it.
"""

import os


def _flag(name: str, default: bool = False) -> bool:
    """Read a boolean environment variable."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def include_estimates() -> bool:
    """Whether stories should carry story point and priority estimates.

    Off by default. The fields are generated and validated but nothing
    downstream consumes them, so producing them spends model attention and
    output tokens for no delivered value. They are also the weakest output the
    pipeline can produce: story point estimation depends on team velocity the
    model has no access to, and prioritisation from an LLM has been reported to
    align only moderately with expert rankings.

    The schema keeps both fields optional, so turning this on restores them
    without any other change.

    Read at prompt-build time rather than at import, so tests and deployments
    can flip it without reimporting the module.
    """
    return _flag("INCLUDE_ESTIMATES", default=False)


def epic_count_range(requirement_count):
    """
    Derive how many epics a requirement set needs.

    The prompts previously asked for "5-10 epics" regardless of input size.
    At twenty-odd requirements that happens to be right, but the number is a
    constant attached to a variable, and the two instructions can contradict
    each other: 10 epics holding at most 5 requirements each is 50 slots, so a
    60-requirement specification is asked to group everything AND to produce
    too few epics to hold it. A model resolving that conflict has to drop
    requirements, and no coverage instruction can save it.

    Deriving the range from the count removes the contradiction: at 3-4
    requirements per epic, n requirements need about n/4 to n/3 epics.

    Returns:
        (low, high) epic counts, always with high > low and low >= 1
    """
    n = max(int(requirement_count or 0), 1)
    low = max(1, round(n / 4))
    high = max(low + 1, round(n / 3))
    return low, high
