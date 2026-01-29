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
from core_engine.prompts import extract_epics
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
    
    def test_no_auth_keywords_in_weather_system(self):
        """Verify no authentication keywords appear in weather system stories"""
        # This would need to be tested with actual LLM generation
        # For now, we verify the prompt has the forbidden features
        import inspect
        
        source = inspect.getsource(extract_epics)
        
        # Verify FORBIDDEN FEATURES are in prompt
        assert "FORBIDDEN FEATURES" in source
        assert "Authentication systems" in source
        assert "User management" in source
        assert "Search functionality" in source


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
        # Clean up any existing file
        if os.path.exists("quality_metrics.jsonl"):
            os.remove("quality_metrics.jsonl")
        
        stories = [{
            "id": 1,
            "source_quote": "test quote",
            "definitionOfDone": "test dod"
        }]
        
        metrics = log_quality_metrics(stories, [])
        
        assert os.path.exists("quality_metrics.jsonl")
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
                "source_quote": "collect weather data from instruments",
                "definitionOfDone": "System collects data successfully"
            },
            {
                "id": 2,
                "source_quote": "transmit via satellite",
                "definitionOfDone": "Data transmitted reliably"
            },
            {
                "id": 3,
                "source_quote": "user authentication required",  # FABRICATED
                "definitionOfDone": "Auth works"
            }
        ]
        
        valid, errors = validate_generated_stories(stories, source)
        
        # Should have 2 valid stories (story 3 rejected)
        assert len(valid) == 2
        assert valid[0]["id"] == 1
        assert valid[1]["id"] == 2
        
        # Should have error for rejected story
        assert any("REJECTED" in str(e) for e in errors)
