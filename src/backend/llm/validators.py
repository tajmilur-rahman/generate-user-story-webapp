"""
Post-processing validation for LLM-generated output.
Catches invented metrics, template test cases, and missing source quotes.
"""
import re
import json


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
    
    # Check for invented metrics
    invented_patterns = [
        (r'\d+%', 'Percentages (e.g., 90%, 95%)'),
        (r'\d+\s*minutes?', 'Time in minutes (e.g., 30 minutes)'),
        (r'\d+\s*seconds?', 'Time in seconds (e.g., 2 seconds)'),
        (r'\d+\s*hours?', 'Time in hours (e.g., 2 hours)'),
        (r'within\s+\d+', 'Time windows (e.g., within 5 minutes)'),
        (r'does not exceed\s+\d+', 'Time limits (e.g., does not exceed 2 seconds)'),
        (r'\d+\s*transmissions?', 'Count metrics (e.g., 30 transmissions)'),
        (r'\d+\s*of\s+components?', 'Percentage-like (e.g., 80% of components)'),
    ]
    
    for pattern, description in invented_patterns:
        matches = re.findall(pattern, json_str, re.IGNORECASE)
        for match in matches:
            # Check if this metric exists in source text
            if source_text and match.lower() not in source_text.lower():
                issues.append(f"Invented metric found: '{match}' ({description})")
            elif not source_text:
                # If no source text provided, flag all matches as potential issues
                issues.append(f"Potential invented metric: '{match}' ({description})")
    
    # Check for template test cases
    template_patterns = [
        r'Functionality works as specified',
        r'Verify that the system must',
        r'works as specified in the user story',
        r'Test cases will be defined',
    ]
    
    for pattern in template_patterns:
        if re.search(pattern, json_str, re.IGNORECASE):
            issues.append(f"Template test case detected: '{pattern}' - not concrete")
    
    # Check for source quote presence in user stories
    if '"User Stories"' in json_str or '"Epics"' in json_str:
        # Try to parse and check for source_basis or source_quote
        try:
            data = json.loads(json_str) if isinstance(json_str, str) else generated_json
            stories = data.get('User Stories', data.get('Epics', []))
            for idx, story in enumerate(stories):
                if isinstance(story, dict):
                    has_source = (
                        'source_basis' in story or 
                        'source_quote' in story or
                        'sourceQuote' in story
                    )
                    if not has_source:
                        issues.append(f"Story {idx + 1} missing source quote/basis for traceability")
        except (json.JSONDecodeError, TypeError):
            # If we can't parse, just check for the field names
            if 'source_basis' not in json_str and 'source_quote' not in json_str:
                issues.append("Missing source quotes for traceability")
    
    # Check for generic deliverables
    generic_deliverables = [
        r'Deliverables:\s*TBD',
        r'No deliverables defined',
        r'Deliverables will be defined',
    ]
    
    for pattern in generic_deliverables:
        if re.search(pattern, json_str, re.IGNORECASE):
            issues.append(f"Generic deliverable placeholder: '{pattern}'")
    
    # Check for concrete test case structure
    if '"testCases"' in json_str or '"Test Cases"' in json_str:
        # Check if test cases have concrete input/output
        if 'input' not in json_str.lower() or 'expected' not in json_str.lower():
            issues.append("Test cases may be missing concrete input/output structure")
    
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
                f"Completeness mismatch: {req_count} requirements but {story_count} user stories. "
                f"Expected {req_count} stories."
            )
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'issue_count': len(issues),
            'requirement_count': req_count,
            'story_count': story_count
        }
    except (json.JSONDecodeError, TypeError, AttributeError) as e:
        issues = [f"Error validating completeness: {str(e)}"]
        return {
            'valid': False,
            'issues': [f"Error validating completeness: {str(e)}"],
            'requirement_count': 0,
            'story_count': 0
        }


def print_validation_report(validation_result, title="Validation Report"):
    """Print a formatted validation report."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    
    if validation_result.get('valid', False):
        print("✅ VALIDATION PASSED")
    else:
        issue_count = validation_result.get('issue_count', len(validation_result.get('issues', [])))
        print(f"❌ VALIDATION FAILED ({issue_count} issues)")
        print("\nIssues found:")
        for i, issue in enumerate(validation_result.get('issues', []), 1):
            print(f"  {i}. {issue}")
    
    print(f"{'='*60}\n")

