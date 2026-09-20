"""
Output contracts for the agent pipeline.

Every agent returns JSON that downstream code indexes into directly. Before
these models existed, a model that returned valid JSON with an unexpected key
surfaced as a KeyError several layers away -- `KeyError: 'description'` once
destroyed a completed three-minute run while building the HTTP response.

Validating at the agent boundary converts that class of defect into a typed,
retryable error raised where the bad output was produced, with a message naming
the offending field. The models are deliberately permissive about extra keys
(models like to add commentary fields) and strict about the keys consumers
actually read.
"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class _Base(BaseModel):
    """Permit unknown extra fields; agents often add commentary keys."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)


def _as_str_list(value: Any) -> List[str]:
    """Coerce a scalar or mixed list into a list of non-empty strings."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return [str(value)]


class Requirement(_Base):
    id: str
    description: str


class RequirementsOutput(_Base):
    requirements: List[Requirement]


class Epic(_Base):
    epic_id: str
    epic_name: str
    # Consumers read epic_description. The converter previously read
    # `description` and raised KeyError on every request.
    epic_description: str = ""
    requirement_ids: List[str] = Field(default_factory=list)


class EpicsOutput(_Base):
    epics: List[Epic]


class Story(_Base):
    story_id: str = ""
    requirement_id: str = ""
    user_story: str
    acceptance_criteria: List[str] = Field(default_factory=list)
    definition_of_done: List[str] = Field(default_factory=list)
    story_points: Optional[Union[int, str]] = None
    priority: str = "MEDIUM"

    # Attached by the orchestrator after generation, not by the model.
    epic_id: str = ""
    epic_name: str = ""

    @field_validator("acceptance_criteria", "definition_of_done", mode="before")
    @classmethod
    def _coerce_lists(cls, v: Any) -> List[str]:
        # Models return these as either a list or a single string.
        return _as_str_list(v)


class StoriesOutput(_Base):
    stories: List[Story]


class TestCase(_Base):
    # test_id is assigned centrally by the orchestrator after fan-in, so
    # whatever the model writes here is advisory only.
    test_id: str = ""
    requirement_id: str = ""
    test_description: str = ""
    test_steps: List[str] = Field(default_factory=list)
    expected_result: str = ""

    @field_validator("test_steps", mode="before")
    @classmethod
    def _coerce_steps(cls, v: Any) -> List[str]:
        return _as_str_list(v)


class TestCasesOutput(_Base):
    test_cases: List[TestCase]


class StoryReview(_Base):
    story_id: str = ""
    total_score: int = 0
    invest_scores: Dict[str, Any] = Field(default_factory=dict)
    issues: List[str] = Field(default_factory=list)
    feedback: str = ""

    @field_validator("total_score", mode="before")
    @classmethod
    def _coerce_score(cls, v: Any) -> int:
        # A judge that returns "93/100" or "93" must not break the gate.
        if isinstance(v, str):
            digits = "".join(c for c in v.split("/")[0] if c.isdigit())
            return int(digits) if digits else 0
        return int(v) if v is not None else 0


class ReviewOutput(_Base):
    story_reviews: List[StoryReview] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)


class RewriteOutput(_Base):
    rewritten_story: Story
    changes_made: List[str] = Field(default_factory=list)
