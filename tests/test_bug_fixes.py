import pytest
import json
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from backend.services.story_service import (
    validate_source_quote,
    detect_incomplete_templates,
    validate_no_metadata_leak,
    validate_generated_stories,
    sanitize_story_output,
    log_quality_metrics,
)
class TestBug1FabricatedQuotes:
    """Bug 1: Stories with fabricated quotes should be REJECTED"""
    
    def test_exact_quote_passes(self):
        source = "The system must collect weather data from instruments"
        quote = "collect weather data from instruments"
        assert validate_source_quote(quote, source) == True
    
    def test_fabricated_quote_fails(self):
        source = "The system must collect weather data from instruments"
        quote = "user authentication is required"
        assert validate_source_quote(quote, source) == False
    
    def test_paraphrased_quote_fails(self):
        source = "The system must collect weather data from instruments"
        quote = "system collects weather information from sensors"
        # This should fail because it's a paraphrase, not exact quote
        assert validate_source_quote(quote, source) == False
    
    def test_stories_with_fabricated_quotes_rejected(self):
        source = "The system collects weather data"
        stories = [{
            "id": 1,
            "source_quote": "user authentication required",
            "definitionOfDone": "Auth implemented"
        }]
        
        valid, errors = validate_generated_stories(stories, source)
        
        assert len(valid) == 0, "Story with fabricated quote should be rejected"
        assert any("Fabricated" in str(e) or "REJECTED" in str(e) for e in errors)


class TestBug2HallucinatedRequirements:
    """Bug 2: Hallucinated features should not appear in output"""
    
    def test_extraction_prompt_forbids_inventing_features(self):
        """The extraction prompt must forbid inventing unstated features.

        Previously asserted against a FORBIDDEN FEATURES block in
        core_engine.prompts.extract_epics. That module no longer exists, and the
        block did not survive the restructure -- this test was uncollectable, so
        nobody noticed. The agentic pipeline enforces the same intent with a
        general instruction in the requirements extractor, which is the live
        guardrail worth protecting.
        """
        import inspect
        from agents.requirements_agent import RequirementsAgent

        source = inspect.getsource(RequirementsAgent.get_system_prompt)

        assert "do NOT invent" in source
        assert "EXTRACT ONLY WHAT IS STATED" in source
        assert "EXPLICITLY mentioned" in source


class TestBug3InventedMetrics:
    """Bug 3: Invented metrics should be removed"""
    
    def test_percentage_metrics_removed(self):
        story = {
            "definitionOfDone": "System achieves 99.9% uptime and 95% success rate"
        }
        
        cleaned = sanitize_story_output(story)
        
        assert "99.9%" not in cleaned["definitionOfDone"]
        assert "95%" not in cleaned["definitionOfDone"]
    
    def test_time_metrics_removed(self):
        story = {
            "definitionOfDone": "Response within 5 minutes and latency under 2 seconds"
        }
        
        cleaned = sanitize_story_output(story)
        
        assert "5 minutes" not in cleaned["definitionOfDone"]
        assert "2 seconds" not in cleaned["definitionOfDone"]
    
    def test_bandwidth_metrics_removed(self):
        story = {
            "definitionOfDone": "Transmission at 100 kbps with 24 hours battery life"
        }
        
        cleaned = sanitize_story_output(story)
        
        assert "100 kbps" not in cleaned["definitionOfDone"]
        assert "24 hours" not in cleaned["definitionOfDone"]


class TestBug4TemplateFailures:
    """Bug 4: Incomplete templates should be detected"""
    
    def test_at_least_comma_detected(self):
        text = "operational for at least ,"
        assert detect_incomplete_templates(text) == True
    
    def test_for_comma_detected(self):
        text = "tested for ,"
        assert detect_incomplete_templates(text) == True
    
    def test_of_comma_detected(self):
        text = "success rate of ,"
        assert detect_incomplete_templates(text) == True
    
    def test_tested_for_after_detected(self):
        text = "tested for after the update"
        assert detect_incomplete_templates(text) == True
    
    def test_valid_text_not_detected(self):
        text = "System operates reliably and efficiently"
        assert detect_incomplete_templates(text) == False


class TestBug5MetadataLeaks:
    """Bug 5: Metadata leaks should be detected"""
    
    def test_source_basis_detected(self):
        story = {
            "definitionOfDone": "• Source Basis: The system must..."
        }
        assert validate_no_metadata_leak(story) == False
    
    def test_deliverables_detected(self):
        story = {
            "definitionOfDone": "Deliverables: {'key': 'value'}"
        }
        assert validate_no_metadata_leak(story) == False
    
    def test_python_dict_detected(self):
        story = {
            "definitionOfDone": "Requirements: {'name': 'test'}"
        }
        assert validate_no_metadata_leak(story) == False
    
    def test_clean_dod_passes(self):
        story = {
            "definitionOfDone": "System successfully implements data collection"
        }
        assert validate_no_metadata_leak(story) == True


class TestBug6QualityMetrics:
    """Bug 6: Quality metrics should be logged"""
    
    def test_quality_metrics_file_created(self):
        # log_quality_metrics writes to data/logs/, not the working directory.
        # The original assertion predates that move.
        project_root = os.path.dirname(os.path.dirname(__file__))
        metrics_file = os.path.join(project_root, "data", "logs",
                                    "quality_metrics.jsonl")
        if os.path.exists(metrics_file):
            os.remove(metrics_file)

        stories = [{
            "id": 1,
            "source_quote": "test quote",
            "definitionOfDone": "test dod"
        }]

        metrics = log_quality_metrics(stories, [])

        assert os.path.exists(metrics_file)
        assert metrics["total_stories"] == 1
        assert "timestamp" in metrics
    
    def test_quality_metrics_content(self):
        stories = [
            {"id": 1, "source_quote": "quote1", "definitionOfDone": "dod1"},
            {"id": 2, "source_quote": "quote2", "definitionOfDone": "dod2"}
        ]
        
        metrics = log_quality_metrics(stories, ["error1", "error2"])
        
        assert metrics["total_stories"] == 2
        assert metrics["validation_errors"] == 2
        assert metrics["stories_with_source_quotes"] == 2
        
        # Verify file contains valid JSON
        metrics_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'logs', 'quality_metrics.jsonl')
        with open(metrics_file, "r") as f:
            lines = f.readlines()
            assert len(lines) > 0
            last_entry = json.loads(lines[-1])
            assert last_entry["total_stories"] == 2


class TestIntegration:
    """Integration tests for complete validation flow"""
    
    def test_complete_validation_flow(self):
        source = "The system must collect weather data from instruments and transmit via satellite"
        
        stories = [
            {
                "id": 1,
                "User Story": "As a meteorologist, I want the system to collect "
                              "weather data from instruments, so that readings "
                              "are captured continuously",
                "Deliverables": {"Collector": {"definition_of_done": "Instrument polling service"}},
                "source_quote": "collect weather data from instruments",
                "definitionOfDone": "System collects data successfully"
            },
            {
                "id": 2,
                "User Story": "As a meteorologist, I want data transmitted via "
                              "satellite, so that readings reach the central "
                              "station",
                "Deliverables": {"Uplink": {"definition_of_done": "Satellite transmission module"}},
                "source_quote": "transmit via satellite",
                "definitionOfDone": "Data transmitted reliably"
            },
            {
                "id": 3,
                "User Story": "As an administrator, I want user authentication, "
                              "so that access is controlled",
                "Deliverables": {"Auth": {"definition_of_done": "Login module"}},
                "source_quote": "user authentication required",  # FABRICATED
                "definitionOfDone": "Auth works"
            }
        ]
        
        valid, errors = validate_generated_stories(stories, source)

        # Fabricated quotes are deliberately a WARNING rather than a rejection.
        # story_service records the reason inline: "Changed to WARNING instead
        # of REJECT ... quote validation is too strict". This test predates that
        # decision and asserted a rejection. What still matters -- and what this
        # now asserts -- is that the fabricated quote is DETECTED and reported.
        assert len(valid) == 3
        assert [story["id"] for story in valid] == [1, 2, 3]

        # Story 3's quote does not appear in the source and must be flagged
        assert any("Story 3" in str(e) and "source quote" in str(e).lower()
                   for e in errors)
        # Stories 1 and 2 quote the source verbatim and must not be flagged
        assert not any("Story 1" in str(e) or "Story 2" in str(e)
                       for e in errors)
