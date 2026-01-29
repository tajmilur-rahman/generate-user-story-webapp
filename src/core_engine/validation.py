"""
Post-processing validation for LLM-generated output.
Basic validation utilities.
"""
import re
import json
import logging

logger = logging.getLogger(__name__)


def validate_output(generated_json, source_text=""):
    """
    Validate generated JSON output for common issues.
    
    Args:
        generated_json: JSON string or dict from LLM
        source_text: Original source text for comparison
    
    Returns:
        dict with 'valid' (bool) and 'issues' (list of strings)
    """
    issues = []
    
    # Convert to string if needed
    if isinstance(generated_json, dict):
        json_str = json.dumps(generated_json, indent=2)
    else:
        json_str = str(generated_json)
    
    # Basic validation - check if it's valid JSON
    try:
        if isinstance(generated_json, str):
            json.loads(generated_json)
    except json.JSONDecodeError as e:
        issues.append(f"Invalid JSON: {str(e)}")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'issue_count': len(issues)
    }


def validate_requirements_completeness(requirements_json, epics_json):
    """
    Validate that all requirements have corresponding user stories.
    
    Args:
        requirements_json: JSON string or dict with requirements
        epics_json: JSON string or dict with user stories/epics
    
    Returns:
        dict with 'valid' (bool) and 'issues' (list of strings)
    """
    issues = []
    
    try:
        # Parse requirements
        if isinstance(requirements_json, str):
            req_data = json.loads(requirements_json)
        else:
            req_data = requirements_json
        
        # Parse epics
        if isinstance(epics_json, str):
            epics_data = json.loads(epics_json)
        else:
            epics_data = epics_json
        
        # Count requirements
        requirements = req_data.get('requirements', [])
        req_count = len(requirements) if isinstance(requirements, list) else 0
        
        # Count user stories
        stories = epics_data.get('User Stories', epics_data.get('Epics', []))
        story_count = len(stories) if isinstance(stories, list) else 0
        
        # Check completeness
        if req_count > 0 and story_count != req_count:
            issues.append(
                f"Completeness mismatch: {req_count} requirements but {story_count} user stories."
            )
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'issue_count': len(issues),
            'requirement_count': req_count,
            'story_count': story_count
        }
    except (json.JSONDecodeError, TypeError, AttributeError) as e:
        return {
            'valid': False,
            'issues': [f"Error validating completeness: {str(e)}"],
            'requirement_count': 0,
            'story_count': 0
        }


def print_validation_report(validation_result, title="Validation Report"):
    """Print a formatted validation report using logger."""
    try:
        logger.info(f"\n{'='*60}")
        logger.info(f"{title}")
        logger.info(f"{'='*60}")
        
        if validation_result.get('valid', False):
            logger.info("[PASS] VALIDATION PASSED")
        else:
            issue_count = validation_result.get('issue_count', len(validation_result.get('issues', [])))
            logger.warning(f"[FAIL] VALIDATION FAILED ({issue_count} issues)")
            logger.warning("Issues found:")
            for i, issue in enumerate(validation_result.get('issues', []), 1):
                logger.warning(f"  {i}. {issue}")
        
        logger.info(f"{'='*60}\n")
    except Exception as e:
        logger.error(f"Error printing validation report: {e}")
