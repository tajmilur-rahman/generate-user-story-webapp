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
