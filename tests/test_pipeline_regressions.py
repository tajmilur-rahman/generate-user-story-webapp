"""
Regression tests for defects fixed in the parallel agentic pipeline.

Every bug these cover was deterministic and reproducible without a model:
character-similarity thresholds discarding distinct requirements, ID collisions
across parallel workers, and mismatched dictionary keys between the orchestrator
and the converter. None needed an LLM to detect, and none would have reached
production with these tests in place.

No test here requires a running Ollama instance.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from agents.orchestrator_parallel import ParallelStoryOrchestrator, _story_core
from backend.services.story_service import (
    _tc_similarity,
    convert_stories_to_frontend_format,
)


@pytest.fixture
def orchestrator():
    """Orchestrator instance without constructing any agents (no LLM needed)."""
    from threading import Lock

    orch = ParallelStoryOrchestrator.__new__(ParallelStoryOrchestrator)
    orch.failures = []
    orch._failures_lock = Lock()
    orch.run_id = None
    orch.run_dir = None
    orch.completed_phases = []
    orch.max_workers = 5
    return orch


class TestRequirementDeduplication:
    """Dedup compared characters, not meaning, and deleted real requirements."""

    def test_distinct_sensors_are_not_merged(self, orchestrator):
        """Pressure, wind speed and wind direction are separate measurements.

        At the original 0.60 SequenceMatcher threshold, "Collect pressure
        readings periodically" scored 0.63 against the temperature requirement
        and wind direction scored 0.86 against wind speed, so all were silently
        discarded along with every story and test case derived from them.
        """
        descriptions = [
            "Collect temperature readings every minute",
            "Calculate and store temperature averages every 5 minutes",
            "Collect pressure readings periodically",
            "Record pressure readings every minute",
            "Collect wind speed readings periodically",
            "Collect wind direction readings periodically",
            "Collect sunshine duration data every 24 hours",
            "Record rainfall volume data every 24 hours",
        ]
        reqs = [{"id": f"REQ-{i:03d}", "description": d}
                for i, d in enumerate(descriptions, 1)]

        result = orchestrator.deduplicate_requirements(reqs)

        assert len(result) == len(reqs), (
            "distinct requirements were merged: "
            f"{set(descriptions) - {r['description'] for r in result}}"
        )

    def test_exact_duplicate_is_still_removed(self, orchestrator):
        """Loosening the threshold must not disable dedup entirely."""
        reqs = [
            {"id": "REQ-001", "description": "Collect temperature readings every minute"},
            {"id": "REQ-002", "description": "Store readings with a timestamp"},
            {"id": "REQ-003", "description": "Collect temperature readings every minute"},
        ]

        result = orchestrator.deduplicate_requirements(reqs)

        assert len(result) == 2
        assert [r["id"] for r in result] == ["REQ-001", "REQ-002"]


class TestStoryDeduplication:
    """Shared persona boilerplate made unrelated stories look similar."""

    def test_persona_prefix_is_stripped_before_comparison(self):
        core = _story_core(
            "As a weather station operator, I want to replace parts, "
            "so that it stays serviceable"
        )
        assert core.startswith("replace parts")
        assert "weather station operator" not in core

    def test_distinct_stories_survive_shared_boilerplate(self, orchestrator):
        """Every story opens with the same ~41 character persona clause.

        The original rule was `title_sim > 0.5 OR desc_sim > 0.7`, and the
        boilerplate alone put unrelated pairs at 50-68%. A story whose
        description was only 3.5% similar -- entirely different work -- was
        dropped on title overlap.
        """
        stories = [
            {"user_story": "As a weather station operator, I want to replace parts "
                           "of the station, so that it stays serviceable",
             "acceptance_criteria": ["Parts can be swapped in the field"]},
            {"user_story": "As a weather station operator, I want to switch backup "
                           "instruments, so that data keeps flowing",
             "acceptance_criteria": ["Backup activates on primary failure"]},
            {"user_story": "As a weather station operator, I want to update the "
                           "embedded software, so that fixes are deployed",
             "acceptance_criteria": ["Firmware updates apply remotely"]},
        ]

        result = orchestrator.deduplicate_stories(stories)

        assert len(result) == 3

    def test_true_duplicate_story_is_removed(self, orchestrator):
        stories = [
            {"user_story": "As an operator, I want to replace parts of the station, "
                           "so that it stays serviceable",
             "acceptance_criteria": ["Parts can be swapped in the field"]},
            {"user_story": "As an operator, I want to replace parts of the station, "
                           "so that it remains serviceable",
             "acceptance_criteria": ["Parts can be swapped in the field"]},
        ]

        result = orchestrator.deduplicate_stories(stories)

        assert len(result) == 1


class TestIdentifierAssignment:
    """Independent workers must not mint IDs in a shared namespace."""

    def test_story_ids_are_unique_across_parallel_epics(self):
        """Each epic is a separate Story Writer call numbering from STORY-001.

        Unnamespaced, `story_map = {s["story_id"]: s}` collapsed 19 stories to
        4 entries: 15 became unreachable by the rewrite pass, and rewriting one
        story overwrote every story sharing its ID.
        """
        epic_sizes = {"EPIC-001": 2, "EPIC-002": 4, "EPIC-003": 2, "EPIC-004": 4,
                      "EPIC-005": 2, "EPIC-006": 2, "EPIC-007": 3}
        stories = []
        for epic_id, count in epic_sizes.items():
            batch = [{"story_id": f"STORY-{i:03d}"} for i in range(1, count + 1)]
            for offset, story in enumerate(batch, start=1):
                story["epic_id"] = epic_id
                story["story_id"] = f"{epic_id}-STORY-{offset:03d}"
            stories.extend(batch)

        ids = [s["story_id"] for s in stories]

        assert len(set(ids)) == len(stories) == 19
        assert len({s["story_id"]: s for s in stories}) == 19

    def test_malformed_test_case_ids_do_not_crash(self, orchestrator):
        """IDs were renumbered via int(test_id.replace('TC', '')).

        'tc1', 'TC_1', 'TC1a' and 'TC01-A' all raise ValueError there, and a
        missing key raises KeyError -- after all five phases had completed.
        """
        reqs = [{"id": f"REQ-{i:03d}"} for i in range(1, 4)]
        batches = {
            0: [{"requirement_id": "REQ-001", "test_id": "tc1"},
                {"requirement_id": "REQ-001", "test_id": "TC_1"}],
            1: [{"requirement_id": "REQ-002", "test_id": "TC01-A"},
                {"requirement_id": "REQ-002"}],
            2: [{"requirement_id": "REQ-003", "test_id": "TC1a"},
                {"requirement_id": "UNKNOWN-REQ", "test_id": "???"}],
        }

        result = orchestrator._assign_test_case_ids(batches, reqs)

        ids = [tc["test_id"] for tc in result]
        assert ids == [f"TC{i}" for i in range(1, len(result) + 1)]
        assert len(set(ids)) == len(ids)

    def test_test_case_ids_do_not_depend_on_completion_order(self, orchestrator):
        """Results were appended as futures completed, so ties resolved by
        thread timing and the same document could yield different orderings."""
        reqs = [{"id": f"REQ-{i:03d}"} for i in range(1, 4)]

        def batches():
            return {
                0: [{"requirement_id": "REQ-001", "test_description": "a"}],
                1: [{"requirement_id": "REQ-002", "test_description": "b"}],
                2: [{"requirement_id": "REQ-003", "test_description": "c"}],
            }

        expected = [(tc["test_id"], tc["test_description"])
                    for tc in orchestrator._assign_test_case_ids(batches(), reqs)]

        for order in ([2, 0, 1], [1, 2, 0], [2, 1, 0]):
            shuffled = {k: batches()[k] for k in order}
            actual = [(tc["test_id"], tc["test_description"])
                      for tc in orchestrator._assign_test_case_ids(shuffled, reqs)]
            assert actual == expected


class TestOrchestratorToConverterContract:
    """The orchestrator hands structured data to a converter with its own shape.

    Three mismatches in this handoff each produced a 500 after a full pipeline
    run: a nested Epics structure the converter read as stories, test case
    groups it could not match, and renamed fields it silently ignored.
    """

    @staticmethod
    def _build_payload(requirements, stories, test_cases):
        """Mirror the conversion the agentic route performs."""
        import json

        epics_json = json.dumps({
            "User Stories": [
                {
                    "User Story": s["user_story"],
                    "Acceptance Criteria": s.get("acceptance_criteria", []),
                    "Deliverables": {
                        "Definition of Done": {
                            "definition_of_done": s.get("definition_of_done", [])
                        }
                    },
                    "Priority": s.get("priority", "Medium"),
                    "Estimation": s.get("story_points", "")
                }
                for s in stories
            ]
        }, indent=2)

        text_by_id = {r["id"]: r["description"] for r in requirements}
        groups = {}
        for tc in test_cases:
            groups.setdefault(tc.get("requirement_id", ""), []).append({
                "id": tc.get("test_id", ""),
                "description": tc.get("test_description", ""),
                "steps": tc.get("test_steps", []),
                "expected_result": tc.get("expected_result", "")
            })

        test_cases_json = json.dumps({
            "test_cases": [
                {"requirement_id": rid,
                 "requirement": text_by_id.get(rid, ""),
                 "test_cases": group}
                for rid, group in groups.items()
            ]
        }, indent=2)

        requirements_text = "\n".join(
            f"{r['id']}: {r['description']}" for r in requirements)
        return epics_json, test_cases_json, requirements_text

    @pytest.fixture
    def pipeline_output(self):
        requirements = [
            {"id": "REQ-001", "description": "Collect temperature readings every minute"},
            {"id": "REQ-002", "description": "Store readings in local database with timestamps"},
        ]
        stories = [
            {"story_id": "EPIC-001-STORY-001", "requirement_id": "REQ-001",
             "epic_id": "EPIC-001",
             "user_story": "As a weather station operator, I want the system to "
                           "automatically record temperature readings, so that I "
                           "have continuous monitoring data",
             "acceptance_criteria": ["Readings captured every 60 seconds"],
             "definition_of_done": ["Sensor polling implemented"],
             "story_points": 3, "priority": "HIGH"},
            {"story_id": "EPIC-001-STORY-002", "requirement_id": "REQ-002",
             "epic_id": "EPIC-001",
             "user_story": "As a weather station operator, I want readings stored "
                           "in a local database with timestamps, so that data "
                           "survives network outages",
             "acceptance_criteria": ["Rows written to readings table"],
             "definition_of_done": ["Schema migration applied"],
             "story_points": 5, "priority": "MEDIUM"},
        ]
        test_cases = [
            {"test_id": "TC1", "requirement_id": "REQ-001",
             "test_description": "Verify temperature readings recorded every minute",
             "test_steps": ["Start station"], "expected_result": "Readings present"},
            {"test_id": "TC2", "requirement_id": "REQ-002",
             "test_description": "Verify readings persisted to local database with timestamps",
             "test_steps": ["Record a reading"], "expected_result": "Row present"},
        ]
        return requirements, stories, test_cases

    def test_stories_survive_conversion(self, pipeline_output):
        """A nested Epics payload made the converter read epics as stories and
        skip all of them, returning 0 stories after a full pipeline run."""
        result = convert_stories_to_frontend_format(
            *self._build_payload(*pipeline_output))

        assert len(result) == 2

    def test_titles_are_distinct(self, pipeline_output):
        """Title generation stripped "The system must" but not the As-a clause,
        so every story rendered as "As Weather Station Operator I"."""
        result = convert_stories_to_frontend_format(
            *self._build_payload(*pipeline_output))

        titles = [story["title"] for story in result]
        assert len(set(titles)) == len(titles)
        assert not any(title.startswith("As ") for title in titles)

    def test_each_story_receives_its_own_test_cases(self, pipeline_output):
        result = convert_stories_to_frontend_format(
            *self._build_payload(*pipeline_output))

        assert "TC1" in result[0]["testCases"]
        assert "TC2" in result[1]["testCases"]


class TestTestCaseSimilarity:
    """Story-to-requirement matching must tolerate asymmetric text lengths."""

    def test_similarity_is_importable(self):
        """_tc_similarity was nested inside convert_stories_to_frontend_format,
        so the orchestrator's import could never resolve and silently fell back
        to a cruder matcher."""
        assert callable(_tc_similarity)

    def test_matching_story_outscores_non_matching(self):
        """Jaccard scored a correct match as low as 0.15 because a terse
        requirement against a verbose story produces a story-dominated union."""
        req_temp = "Collect temperature readings every minute"
        req_store = "Store readings in local database with timestamps"
        story_temp = ("As a weather station operator, I want the system to "
                      "automatically record temperature readings, so that I have "
                      "continuous monitoring data")

        assert _tc_similarity(req_temp, story_temp) >= 0.35
        assert _tc_similarity(req_store, story_temp) < 0.35


class TestPartialFailureReporting:
    """A run that lost an epic must not look identical to a complete one."""

    def test_failures_are_recorded_thread_safely(self, orchestrator):
        from threading import Thread

        threads = [
            Thread(target=orchestrator._record_failure,
                   args=("stories", f"epic {i}", "boom"))
            for i in range(50)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(orchestrator.failures) == 50
        assert all(f["phase"] == "stories" for f in orchestrator.failures)


class TestCheckpointing:
    """A failure late in the pipeline must not discard completed phases."""

    def test_phase_output_is_persisted(self, orchestrator, tmp_path):
        import json

        orchestrator.run_dir = str(tmp_path / "run-1")
        orchestrator._checkpoint("01_requirements",
                                 [{"id": "REQ-001", "description": "x"}])

        written = tmp_path / "run-1" / "01_requirements.json"
        assert written.exists()
        assert json.loads(written.read_text(encoding="utf-8"))[0]["id"] == "REQ-001"
        assert orchestrator.completed_phases == ["01_requirements"]

    def test_unwritable_checkpoint_does_not_fail_the_run(self, orchestrator):
        """Persisting is best-effort; it must never take down a good run."""
        orchestrator.run_dir = os.path.join("Z:", "nonexistent", "path")

        orchestrator._checkpoint("01_requirements", [{"id": "REQ-001"}])

        assert orchestrator.completed_phases == ["01_requirements"]


class TestDeterministicQualityGate:
    """The model judge returned a constant 93/100 and never failed a story,
    so the rewrite path never ran and a corruption bug stayed latent there."""

    @staticmethod
    def _story(**overrides):
        story = {
            "story_id": "EPIC-001-STORY-001",
            "requirement_id": "REQ-001",
            "user_story": "As a weather station operator, I want the system to "
                          "record temperature readings, so that I have "
                          "continuous monitoring data",
            "acceptance_criteria": ["Readings captured every 60 seconds"],
            "definition_of_done": ["Sensor polling implemented"],
        }
        story.update(overrides)
        return story

    def test_well_formed_story_passes(self):
        from agents.invest_checks import evaluate_story

        assert evaluate_story(self._story())["score"] == 100

    @pytest.mark.parametrize("overrides,expected_issue", [
        ({"user_story": "The system must record temperature readings"},
         "does not follow"),
        ({"acceptance_criteria": []}, "No acceptance criteria"),
    ])
    def test_critical_failures_cross_the_rewrite_threshold(self, overrides,
                                                           expected_issue):
        """A rule-detectable failure must send the story back, whatever the
        model judge says about it."""
        from agents.invest_checks import evaluate_story

        result = evaluate_story(self._story(**overrides))

        assert result["score"] < 70
        assert any(expected_issue in issue for issue in result["issues"])

    @pytest.mark.parametrize("overrides,expected_issue", [
        ({"acceptance_criteria": ["works", "done"]}, "Vague acceptance criteria"),
        ({"requirement_id": ""}, "does not reference a requirement"),
        ({"definition_of_done": []}, "No deliverables or definition of done"),
    ])
    def test_soft_signals_flag_without_forcing_a_rewrite(self, overrides,
                                                         expected_issue):
        from agents.invest_checks import evaluate_story

        result = evaluate_story(self._story(**overrides))

        assert result["score"] >= 70
        assert any(expected_issue in issue for issue in result["issues"])

    def test_deliverables_satisfy_the_definition_of_done_check(self):
        """Stories now carry work as categorised `deliverables`; the flat
        `definition_of_done` list is only a fallback for older payloads."""
        from agents.invest_checks import evaluate_story

        story = self._story(definition_of_done=[])
        story["deliverables"] = {
            "architecture_design": ["Design doc for data_collection_module"],
            "unit_tests": ["Unit tests for scheduler.poll()"],
        }

        result = evaluate_story(story)

        assert result["score"] == 100
        assert not any("definition of done" in issue.lower()
                       for issue in result["issues"])

    def test_weights_sum_to_one_hundred(self):
        from agents.invest_checks import _WEIGHTS

        assert sum(_WEIGHTS.values()) == 100

    def test_stories_without_ids_do_not_collide(self):
        """A missing story_id must not collapse two stories onto one result."""
        from agents.invest_checks import evaluate_stories

        results = evaluate_stories([self._story(story_id=""),
                                    self._story(story_id="")])

        assert len(results) == 2

    def test_constant_judge_scores_are_detectable(self):
        """A judge returning the same number for everything looks identical to
        a uniform batch if only the mean is reported."""
        from agents.invest_checks import summarise_scores

        constant = summarise_scores([93] * 5)
        varied = summarise_scores([55, 70, 82, 93, 60])

        assert constant["distinct_values"] == 1 and constant["spread"] == 0
        assert varied["distinct_values"] == 5 and varied["spread"] == 38


class TestDefinitionOfDoneFormat:
    """DoD must show deliverable categories with nested items, and must NOT
    restate acceptance criteria.

    The converter folds an "Acceptance Criteria" key into the definitionOfDone
    field, so the agentic route deliberately stops passing it. Sanitisation
    also used to flatten the whole field onto one line, destroying the
    headings.
    """

    @staticmethod
    def _render(story):
        import json
        from backend.routes.api_agentic import _build_deliverables

        payload = json.dumps({"User Stories": [{
            "User Story": story["user_story"],
            "Deliverables": _build_deliverables(story),
        }]})
        result = convert_stories_to_frontend_format(
            payload, json.dumps({"test_cases": []}), "REQ-001: x")
        return result[0]["definitionOfDone"]

    @pytest.fixture
    def story(self):
        return {
            "user_story": "As a weather station operator, I want readings "
                          "collected, so that data is captured",
            "acceptance_criteria": [
                "Given powered on, When time elapses, Then a reading is recorded"],
            "deliverables": {
                "architecture_design": [
                    "Architecture diagram showing data_collection_module and scheduler",
                    "Design reviewed and approved by technical lead"],
                "database_schema_design": [
                    "Schema: reading_id, sensor_type, timestamp, value"],
                "unit_tests": [
                    "Unit tests for scheduler.poll()",
                    "All tests passing in CI/CD pipeline"],
            },
        }

    def test_acceptance_criteria_are_not_in_definition_of_done(self, story):
        rendered = self._render(story)

        assert "Acceptance Criteria" not in rendered
        assert "Given powered on" not in rendered

    def test_each_category_becomes_a_heading(self, story):
        rendered = self._render(story)

        for heading in ("Architecture Design", "Database Schema Design",
                        "Unit Tests"):
            assert heading in rendered

    def test_items_stay_nested_under_their_heading(self, story):
        """A blanket whitespace collapse flattened this onto one line."""
        rendered = self._render(story)
        lines = [line for line in rendered.split("\n") if line.strip()]

        assert len(lines) > 1, f"definitionOfDone was flattened: {rendered!r}"

        heading_idx = next(i for i, line in enumerate(lines)
                           if "Architecture Design" in line)
        following = lines[heading_idx + 1]
        assert following.startswith(" "), "nested item lost its indentation"
        assert "Architecture diagram" in following

    def test_flat_definition_of_done_still_renders(self):
        """Older payloads sent a flat list with no categories."""
        rendered = self._render({
            "user_story": "As a x, I want y, so that z",
            "definition_of_done": ["Schema migration applied", "Unit tests pass"],
        })

        assert "Schema migration applied" in rendered


class TestDeduplicationBlocking:
    """Similarity comparison must be blocked on requirement id.

    Surface similarity cannot separate distinct stories from duplicates here:
    measured on real output, "record temperature readings" scores 0.905 against
    "record pressure readings" (distinct), while a genuinely reworded duplicate
    scores 0.545 -- the ordering is inverted, so no threshold works. Stories
    tracing to different requirements are therefore never compared at all.
    """

    TEMP = ("As a weather station operator, I want the system to automatically "
            "record temperature readings, so that I have continuous monitoring data")
    PRESSURE = ("As a weather station operator, I want the system to automatically "
                "record pressure readings, so that I have continuous monitoring data")
    TEMP_REWORDED = ("As a weather station operator, I want the system to automatically "
                     "record temperature readings, so that continuous monitoring "
                     "data is available")

    # --- orchestrator layer -------------------------------------------------

    def test_engine_keeps_stories_from_different_requirements(self, orchestrator):
        stories = [
            {"requirement_id": "REQ-001", "user_story": self.TEMP,
             "acceptance_criteria": ["Reading captured every 60 seconds"]},
            {"requirement_id": "REQ-002", "user_story": self.PRESSURE,
             "acceptance_criteria": ["Reading captured every 60 seconds"]},
        ]

        assert len(orchestrator.deduplicate_stories(stories)) == 2

    def test_engine_removes_reworded_duplicate_within_a_requirement(self, orchestrator):
        stories = [
            {"requirement_id": "REQ-001", "user_story": self.TEMP,
             "acceptance_criteria": ["Reading captured every 60 seconds"]},
            {"requirement_id": "REQ-001", "user_story": self.TEMP_REWORDED,
             "acceptance_criteria": ["Reading captured every 60 seconds"]},
        ]

        assert len(orchestrator.deduplicate_stories(stories)) == 1

    # --- presentation layer -------------------------------------------------

    def test_presentation_keeps_stories_from_different_requirements(self):
        from backend.services.story_service import remove_duplicate_stories

        stories = [
            {"User Story": self.TEMP, "Requirement ID": "REQ-001"},
            {"User Story": self.PRESSURE, "Requirement ID": "REQ-002"},
        ]

        assert len(remove_duplicate_stories(stories)) == 2

    def test_presentation_removes_reworded_duplicate_within_a_requirement(self):
        from backend.services.story_service import remove_duplicate_stories

        stories = [
            {"User Story": self.TEMP, "Requirement ID": "REQ-001"},
            {"User Story": self.TEMP_REWORDED, "Requirement ID": "REQ-001"},
        ]

        assert len(remove_duplicate_stories(stories)) == 1

    def test_identical_text_is_removed_across_requirements(self):
        """Identical text is a duplicate by definition, not a similarity call,
        so blocking must not preserve it."""
        from backend.services.story_service import remove_duplicate_stories

        stories = [
            {"User Story": self.TEMP, "Requirement ID": "REQ-001"},
            {"User Story": self.TEMP, "Requirement ID": "REQ-009"},
        ]

        assert len(remove_duplicate_stories(stories)) == 1

    def test_stories_without_requirement_ids_still_deduplicate(self):
        """The legacy path supplies no requirement ids; behaviour there is
        unchanged."""
        from backend.services.story_service import remove_duplicate_stories

        stories = [{"User Story": self.TEMP}, {"User Story": self.TEMP_REWORDED}]

        assert len(remove_duplicate_stories(stories)) == 1

    # --- end to end ---------------------------------------------------------

    @staticmethod
    def _sensor_story(requirement_id, sensor):
        return {
            "requirement_id": requirement_id,
            "user_story": ("As a weather station operator, I want the system to "
                           f"automatically record {sensor} readings, so that I "
                           "have continuous monitoring data"),
            "deliverables": {"unit_tests": [f"Unit tests for {sensor}_driver.read()"]},
        }

    def test_distinct_sensor_stories_survive_the_full_conversion(self):
        """Three stories differing only by sensor name must all reach the user.

        Without the requirement id carried through, token overlap merges them
        and two of the three are silently discarded.
        """
        import json
        from backend.routes.api_agentic import _build_deliverables

        stories = [self._sensor_story("REQ-001", "temperature"),
                   self._sensor_story("REQ-002", "pressure"),
                   self._sensor_story("REQ-003", "wind speed")]

        payload = json.dumps({"User Stories": [
            {"User Story": s["user_story"],
             "Requirement ID": s["requirement_id"],
             "Deliverables": _build_deliverables(s)}
            for s in stories
        ]})

        result = convert_stories_to_frontend_format(
            payload, json.dumps({"test_cases": []}), "REQ-001: Collect readings")

        assert len(result) == 3, (
            "distinct sensor stories were merged: "
            f"{[s['title'] for s in result]}"
        )


class TestAgentPromptsBuild:
    """Every agent must be able to build its prompt.

    RewriterAgent could not. Written inline in an f-string,
    `review.get('invest_scores', {{}})` parses its default as a set literal
    containing an empty dict, which is unhashable, so the call raised
    TypeError every time. The rewrite path therefore never ran. It went
    unnoticed because the model judge always scored above the rewrite
    threshold, so the path was never reached.
    """

    CONTEXT = {
        "document_text": "doc",
        "requirements": [{"id": "REQ-001", "description": "Collect readings"}],
        "requirements_batch": [{"id": "REQ-001", "description": "Collect readings"}],
        "epic": {"epic_id": "EPIC-001", "epic_name": "Data Collection"},
        "raw_epics": [],
        "stories": [{"story_id": "S1", "user_story": "As a x, I want y, so that z"}],
        "story": {"story_id": "S1", "user_story": "As a x, I want y, so that z"},
        "review": {"total_score": 55, "issues": ["vague criteria"],
                   "invest_scores": {"testable": 4}},
        "starting_tc_number": 1,
    }

    @staticmethod
    def _agents():
        from agents.requirements_agent import RequirementsAgent
        from agents.epic_extractor_agent import EpicExtractorAgent
        from agents.epic_refiner_agent import EpicRefinerAgent
        from agents.story_agent import StoryAgent
        from agents.test_agent import TestCaseAgent
        from agents.reviewer_agent import ReviewerAgent
        from agents.rewriter_agent import RewriterAgent
        return [RequirementsAgent, EpicExtractorAgent, EpicRefinerAgent,
                StoryAgent, TestCaseAgent, ReviewerAgent, RewriterAgent]

    def test_every_agent_builds_its_prompt(self):
        for agent_cls in self._agents():
            agent = agent_cls.__new__(agent_cls)
            prompt = agent.get_system_prompt(self.CONTEXT)
            assert prompt and len(prompt) > 100, f"{agent_cls.__name__} built no prompt"

    def test_rewriter_builds_with_an_empty_review(self):
        """The failure mode was in a `.get` default, so a review missing the
        optional keys is the case that must not raise."""
        from agents.rewriter_agent import RewriterAgent

        agent = RewriterAgent.__new__(RewriterAgent)
        prompt = agent.get_system_prompt(
            {"story": {"user_story": "As a x, I want y, so that z"}, "review": {}})

        assert len(prompt) > 100

    def test_rewriter_renders_review_feedback_into_the_prompt(self):
        """A rewrite driven by feedback the model never sees is pointless."""
        from agents.rewriter_agent import RewriterAgent

        agent = RewriterAgent.__new__(RewriterAgent)
        prompt = agent.get_system_prompt(self.CONTEXT)

        assert "vague criteria" in prompt
        assert "testable" in prompt


class TestEstimateToggle:
    """Story points and priority are generated only when enabled.

    Nothing downstream consumes either field, so by default they are kept out
    of the prompt rather than produced and discarded.
    """

    CONTEXT = {
        "requirements_batch": [{"id": "REQ-001", "description": "Collect readings"}],
        "epic": {"epic_id": "EPIC-001", "epic_name": "Data Collection"},
        "story": {"story_id": "S1", "priority": "HIGH", "story_points": 5,
                  "user_story": "As a x, I want y, so that z"},
        "review": {"total_score": 55},
    }

    @staticmethod
    def _prompts(monkeypatch, enabled):
        from agents.story_agent import StoryAgent
        from agents.rewriter_agent import RewriterAgent

        if enabled:
            monkeypatch.setenv("INCLUDE_ESTIMATES", "true")
        else:
            monkeypatch.delenv("INCLUDE_ESTIMATES", raising=False)

        writer = StoryAgent.__new__(StoryAgent)
        rewriter = RewriterAgent.__new__(RewriterAgent)
        return (writer.get_system_prompt(TestEstimateToggle.CONTEXT),
                rewriter.get_system_prompt(TestEstimateToggle.CONTEXT))

    def test_estimates_absent_by_default(self, monkeypatch):
        writer, rewriter = self._prompts(monkeypatch, enabled=False)

        assert "story_points" not in writer
        assert "story_points" not in rewriter

    def test_estimates_restored_when_enabled(self, monkeypatch):
        writer, rewriter = self._prompts(monkeypatch, enabled=True)

        assert "story_points" in writer
        assert "story_points" in rewriter

    @pytest.mark.parametrize("enabled", [False, True])
    def test_critical_rule_numbering_stays_contiguous(self, monkeypatch, enabled):
        """Removing a rule must not leave a gap or a duplicate number."""
        import re

        writer, _ = self._prompts(monkeypatch, enabled=enabled)
        numbers = [int(n) for n in
                   re.findall(r"^(\d+)\.", writer[writer.find("CRITICAL RULES"):], re.M)]

        assert numbers == list(range(1, len(numbers) + 1)), numbers


class TestRetryBehaviour:
    """Agent calls are retried, and parse/validation happen INSIDE the retried
    unit.

    Retry is invisible when it works, so nothing in the output reveals that it
    has been removed. The subtle property is composition: validating after
    invoke() returns looks tidier but leaves schema violations -- the most
    common failure -- unretried.

    These tests substitute the model BEFORE BaseAgent composes its chain, so
    the composition under test is the real one. Replacing `agent._chain`
    afterwards would test LangChain's retry rather than this code, and would
    pass even with retry removed entirely.
    """

    GOOD = '{"epics":[{"epic_id":"EPIC-001","epic_name":"Data","epic_description":"d","requirement_ids":[]}]}'
    MISSING_ID = '{"epics":[{"epic_name":"no id"}]}'

    @staticmethod
    def _agent_with_scripted_model(monkeypatch, responses, output_model=None):
        """Build a real agent whose model returns `responses` in order.

        Returns (agent, calls) where calls["n"] counts model invocations.
        """
        import agents.base_agent as base_agent
        from langchain_core.runnables import RunnableLambda

        calls = {"n": 0}

        def fake_chat_ollama(**kwargs):
            def call(_prompt):
                index = calls["n"]
                calls["n"] += 1
                item = responses[min(index, len(responses) - 1)]
                if isinstance(item, Exception):
                    raise item
                return item
            return RunnableLambda(call)

        monkeypatch.setattr(base_agent, "ChatOllama", fake_chat_ollama)

        class _Agent(base_agent.BaseAgent):
            def get_system_prompt(self, context):
                return "prompt"

        return _Agent("Test Agent", "role", "goal",
                      output_model=output_model), calls

    def test_transient_failure_is_retried_and_then_succeeds(self, monkeypatch):
        agent, calls = self._agent_with_scripted_model(
            monkeypatch, [RuntimeError("connection reset"), '{"requirements": []}'])

        result = agent.run("task", {})

        assert result["success"] is True
        assert calls["n"] == 2, "the failed attempt was not retried"

    def test_persistent_failure_stops_after_max_attempts(self, monkeypatch):
        agent, calls = self._agent_with_scripted_model(
            monkeypatch, [RuntimeError("ollama is down")])

        result = agent.run("task", {})

        assert result["success"] is False
        assert result["attempts"] == agent.max_attempts
        assert calls["n"] == agent.max_attempts, "retried the wrong number of times"
        assert result["error_type"] == "RuntimeError"

    def test_schema_violation_is_retried_not_just_transport_failure(self, monkeypatch):
        """The property most easily lost in a refactor: validation must sit
        inside the retried unit, not after it."""
        from agents.schemas import EpicsOutput

        agent, calls = self._agent_with_scripted_model(
            monkeypatch, [self.MISSING_ID, self.GOOD], output_model=EpicsOutput)

        result = agent.run("task", {})

        assert result["success"] is True, "a contract violation was not retried"
        assert calls["n"] == 2

    def test_exhausted_schema_violation_names_the_offending_field(self, monkeypatch):
        from agents.schemas import EpicsOutput

        agent, _ = self._agent_with_scripted_model(
            monkeypatch, [self.MISSING_ID], output_model=EpicsOutput)

        result = agent.run("task", {})

        assert result["success"] is False
        assert "epic_id" in result["error"], result["error"]

    def test_attempt_count_is_configurable(self, monkeypatch):
        monkeypatch.setenv("OLLAMA_MAX_ATTEMPTS", "2")

        agent, calls = self._agent_with_scripted_model(
            monkeypatch, [RuntimeError("down")])
        agent.run("task", {})

        assert agent.max_attempts == 2
        assert calls["n"] == 2

    def test_calls_are_bounded_by_a_timeout(self, monkeypatch):
        """A stalled call never raises, so it can never be retried. The
        transport timeout is what turns a hang into a retryable failure.

        Uses the real ChatOllama: construction opens no connection.
        """
        monkeypatch.setenv("OLLAMA_TIMEOUT", "42")
        monkeypatch.setenv("OLLAMA_CONNECT_TIMEOUT", "7")

        from agents.base_agent import BaseAgent

        class _Agent(BaseAgent):
            def get_system_prompt(self, context):
                return "prompt"

        timeout = _Agent("Test", "role", "goal").llm.client_kwargs["timeout"]

        assert timeout.read == 42.0
        assert timeout.connect == 7.0


class TestTestCaseMatching:
    """Stories are matched to test cases by requirement id, not text similarity.

    Both sides carry the id, so the link is known rather than inferred.
    Inferring it produced three failure modes in a real run: stories scoring
    below the threshold received no test cases (3 of 16), greedy first-come
    claiming gave a humidity story test cases covering sunshine, rainfall and
    wind, and unclaimed groups were silently dropped (7 test cases orphaned).
    """

    STORIES = [
        ("REQ-001", "As a weather station operator, I want the system to "
                    "automatically record temperature readings, so that I have "
                    "monitoring data"),
        ("REQ-002", "As a system administrator, I want to update the software "
                    "components dynamically, so that the system stays current"),
        ("REQ-003", "As a weather station operator, I want the system to store "
                    "weather data persistently with timestamps, so that I have "
                    "a historical record"),
    ]
    REQUIREMENTS = {
        "REQ-001": "Collect temperature readings every minute",
        "REQ-002": "Support dynamic software component replacement",
        "REQ-003": "Store readings persistently with timestamps",
    }

    @classmethod
    def _convert(cls, carry_requirement_id=True):
        import json
        from backend.routes.api_agentic import _build_deliverables

        deliverables = _build_deliverables({"deliverables": {"unit_tests": ["t"]}})
        payload = {"User Stories": []}
        for requirement_id, text in cls.STORIES:
            story = {"User Story": text, "Deliverables": deliverables}
            if carry_requirement_id:
                story["Requirement ID"] = requirement_id
            payload["User Stories"].append(story)

        test_cases = {"test_cases": [
            {"requirement_id": rid, "requirement": desc,
             "test_cases": [{"id": f"TC-{rid}", "description": f"Verify {desc}",
                             "steps": ["step"], "expected_result": "ok"}]}
            for rid, desc in cls.REQUIREMENTS.items()
        ]}

        return convert_stories_to_frontend_format(
            json.dumps(payload), json.dumps(test_cases),
            "\n".join(f"{k}: {v}" for k, v in cls.REQUIREMENTS.items()))

    def test_every_story_receives_its_own_requirements_test_cases(self):
        result = self._convert()

        assert len(result) == len(self.STORIES)
        for story, (requirement_id, _) in zip(result, self.STORIES):
            assert f"TC-{requirement_id}" in story["testCases"], (
                f"{requirement_id} got: {story['testCases'][:60]}")

    def test_no_story_is_left_without_test_cases(self):
        result = self._convert()

        bare = [s["title"] for s in result if s["testCases"].strip() == "-"]
        assert not bare, f"stories with no test cases: {bare}"

    def test_a_story_is_never_given_another_requirements_test_cases(self):
        result = self._convert()

        for story, (requirement_id, _) in zip(result, self.STORIES):
            others = [f"TC-{r}" for r in self.REQUIREMENTS if r != requirement_id]
            for wrong in others:
                assert wrong not in story["testCases"], (
                    f"{requirement_id} was given {wrong}")

    def test_several_stories_may_share_one_requirements_test_cases(self):
        """One requirement can yield several stories; its test cases apply to
        all of them. Withholding them from every story but the first is what
        left stories bare."""
        import json
        from backend.routes.api_agentic import _build_deliverables

        deliverables = _build_deliverables({"deliverables": {"unit_tests": ["t"]}})
        payload = {"User Stories": [
            {"User Story": "As an operator, I want readings recorded, so that data exists",
             "Requirement ID": "REQ-001", "Deliverables": deliverables},
            {"User Story": "As an analyst, I want readings retained, so that trends emerge",
             "Requirement ID": "REQ-001", "Deliverables": deliverables},
        ]}
        test_cases = {"test_cases": [
            {"requirement_id": "REQ-001", "requirement": "Collect readings",
             "test_cases": [{"id": "TC-1", "description": "Verify collection",
                             "steps": ["s"], "expected_result": "ok"}]}
        ]}

        result = convert_stories_to_frontend_format(
            json.dumps(payload), json.dumps(test_cases), "REQ-001: Collect readings")

        assert len(result) == 2
        assert all("TC-1" in s["testCases"] for s in result)


class TestTitleDerivation:
    """Titles derived from story text must read as titles.

    Four faults appeared in generated output. The deriver works on sentence
    structure and English function words only -- no product names, no domain
    vocabulary -- so these hold for any document. The previous version
    hardcoded prefixes such as "The Insulin Pump system must ", which worked
    for one specification and did nothing for any other.
    """

    STORY = ("As a weather station operator, I want the system to {action} "
             "using [specific elements: sensor, timestamp], so that I have data")

    @staticmethod
    def _derive(text):
        from backend.services.story_service import derive_title
        return derive_title(text)

    def test_title_never_ends_on_a_connective(self):
        """Produced "... Conditions Using" and "... Animals Using"."""
        for action in ["withstand outdoor/exposed conditions",
                       "resist damage by animals",
                       "transmit readings to the archive"]:
            title = self._derive(self.STORY.format(action=action))
            last = title.split()[-1].lower()
            assert last not in {"using", "with", "by", "to", "from", "for",
                                "and", "or", "of", "in", "on", "at"}, title

    def test_title_has_no_repeated_word(self):
        """Produced "Receive Aggregated Weather Data Weather"."""
        title = self._derive(
            "As a data management system, I want to receive aggregated weather "
            "data from the weather station, so that I can store it")
        words = [w.lower() for w in title.split()]

        assert len(words) == len(set(words)), title

    def test_title_does_not_begin_with_a_generic_subject(self):
        """Produced "System Calculate Store Pressure Averages"."""
        title = self._derive(self.STORY.format(
            action="calculate and store pressure averages"))

        assert not title.lower().startswith("system"), title

    def test_title_does_not_strand_a_fragment(self):
        """Stripping a preposition left its object behind: "at rest" became
        "... Records Rest", "on behalf of a member" became "... Behalf Member".
        """
        assert not self._derive(
            "The system must encrypt stored patient records at rest, so that "
            "confidentiality is preserved").lower().endswith("rest")
        assert "behalf" not in self._derive(
            "As a librarian, I want to renew a borrowed item on behalf of a "
            "member, so that fines are avoided").lower()

    @pytest.mark.parametrize("story,forbidden", [
        ("As a clinician, I want the system to deliver a basal insulin dose "
         "every ten minutes, so that the patient stays in range", "ten"),
        ("As a security officer, I want the platform to record every door "
         "access event, so that entry can be audited", "platform"),
    ])
    def test_behaviour_holds_on_unrelated_domains(self, story, forbidden):
        """No weather vocabulary exists in the deriver, so an insulin pump or a
        door access system must behave the same way."""
        title = self._derive(story)

        assert title
        assert forbidden not in title.lower(), title

    def test_a_model_written_title_is_preferred_over_derivation(self):
        import json
        from backend.routes.api_agentic import _build_deliverables

        payload = json.dumps({"User Stories": [{
            "User Story": self.STORY.format(action="calculate pressure averages"),
            "Title": "Average Barometric Pressure",
            "Deliverables": _build_deliverables({"deliverables": {"unit_tests": ["t"]}}),
        }]})

        result = convert_stories_to_frontend_format(
            payload, json.dumps({"test_cases": []}), "REQ-001: x")

        assert result[0]["title"] == "Average Barometric Pressure"

    @pytest.mark.parametrize("text", ["", "   ", "the and of to"])
    def test_unusable_input_yields_no_title(self, text):
        assert self._derive(text) == ""


class TestSourceGrounding:
    """Document-agnostic grounding measures: keyword injection and reporting.

    An extractor run against a wilderness weather station specification
    produced requirements for humidity readings and light intensity control;
    neither word occurs anywhere in the source. Both measures here derive
    everything from the document supplied at runtime, so they configure
    nothing and behave the same on any input.

    Neither removes anything. An earlier filtering attempt was reverted
    (0f7990d) because its threshold rested on a single document.
    """

    @pytest.fixture(scope="class")
    def documents(self):
        from docx import Document

        base = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                            "src", "autoAgile", "tests", "docs")
        names = ["Wilderness_Weather_Station.docx", "insulinPump.docx",
                 "patientInformationSystem.docx"]
        return {n: "\n".join(p.text for p in Document(os.path.join(base, n)).paragraphs)
                for n in names}

    def test_keywords_reflect_each_document(self, documents):
        """No vocabulary is configured, so each document yields its own."""
        from agents.grounding import source_keywords

        weather = source_keywords(documents["Wilderness_Weather_Station.docx"])
        insulin = source_keywords(documents["insulinPump.docx"])
        patient = source_keywords(documents["patientInformationSystem.docx"])

        assert "weather" in weather and "insulin" not in weather
        assert "insulin" in insulin and "weather" not in insulin
        assert "patient" in patient or "patients" in patient
        assert not set(weather) & set(insulin), "keyword sets should not overlap"

    def test_keywords_are_deterministic(self, documents):
        """The same document must always yield the same list."""
        from agents.grounding import source_keywords

        text = documents["insulinPump.docx"]
        assert source_keywords(text) == source_keywords(text)

    def test_keywords_exclude_generic_specification_vocabulary(self, documents):
        from agents.grounding import source_keywords

        keywords = source_keywords(documents["Wilderness_Weather_Station.docx"], 30)

        for generic in ("system", "systems", "data", "requirements", "software"):
            assert generic not in keywords, f"{generic} carries no subject signal"

    def test_empty_document_yields_no_keywords(self):
        from agents.grounding import source_keywords

        assert source_keywords("") == []

    def test_prompt_names_the_documents_own_subjects(self, documents):
        """The instruction alone was ignored; the prompt must state the scope."""
        from agents.requirements_agent import RequirementsAgent

        agent = RequirementsAgent.__new__(RequirementsAgent)
        prompt = agent.get_system_prompt(
            {"document": documents["insulinPump.docx"]})

        assert "SUBJECTS PRESENT IN THIS DOCUMENT" in prompt
        assert "insulin" in prompt.split("SUBJECTS PRESENT")[1][:400]

    def test_prompt_is_safe_without_a_document(self):
        from agents.requirements_agent import RequirementsAgent

        agent = RequirementsAgent.__new__(RequirementsAgent)
        prompt = agent.get_system_prompt({"document": ""})

        assert "SUBJECTS PRESENT IN THIS DOCUMENT" not in prompt
        assert len(prompt) > 100

    def test_invented_subjects_are_reported_as_unsupported(self, documents):
        from agents.grounding import assess_grounding

        source = documents["Wilderness_Weather_Station.docx"]

        humidity = assess_grounding(
            "Record Store Humidity | record and store humidity readings", source)
        light = assess_grounding(
            "Monitor Light Intensity | monitor and adjust light intensity", source)

        assert "humidity" in humidity["unsupported_terms"]
        assert "light" in light["unsupported_terms"]
        assert "intensity" in light["unsupported_terms"]

    def test_genuine_subjects_are_not_reported(self, documents):
        from agents.grounding import assess_grounding

        source = documents["Wilderness_Weather_Station.docx"]
        report = assess_grounding(
            "Record Temperature Readings | record temperature and pressure "
            "readings from the instruments", source)

        for term in ("temperature", "pressure", "instruments", "readings"):
            assert term not in report["unsupported_terms"], report

    def test_grounding_reports_rather_than_judges(self, documents):
        """No verdict is published: a ratio was measured not to separate the
        two populations, so asserting one would be false precision."""
        from agents.grounding import assess_grounding

        report = assess_grounding("anything at all", documents["insulinPump.docx"])

        assert set(report) == {"score", "unsupported_terms"}
        assert "confidence" not in report

    def test_grounding_is_inert_without_a_source(self):
        from agents.grounding import assess_grounding

        assert assess_grounding("some story text", "")["unsupported_terms"] == []
