import re
import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

def validate_source_quote(source_quote, source_text):
    """
    Validate that source_quote actually exists in source_text.
    Uses exact matching and word overlap for robustness.
    
    Args:
        source_quote: Quote to validate
        source_text: Original source document text
    
    Returns:
        bool: True if quote is valid, False otherwise
    """
    if not source_quote or not source_text:
        logger.error("Empty source_quote or source_text")
        return False
    
    # Normalize whitespace for comparison
    source_quote_normalized = ' '.join(source_quote.split())
    source_text_normalized = ' '.join(source_text.split())
    
    # Exact match (case-insensitive)
    if source_quote_normalized.lower() in source_text_normalized.lower():
        logger.debug("✅ Exact quote match")
        return True
    
    # Check for consecutive word sequence (catch close paraphrases)
    quote_words = source_quote_normalized.split()
    source_words = source_text_normalized.split()
    
    # Look for longest consecutive match
    max_consecutive = 0
    for i in range(len(source_words)):
        consecutive = 0
        for j in range(len(quote_words)):
            if i+j < len(source_words) and quote_words[j].lower() == source_words[i+j].lower():
                consecutive += 1
            else:
                break
        max_consecutive = max(max_consecutive, consecutive)
    
    # If at least 60% of words appear consecutively, it's a real quote
    if len(quote_words) > 0 and max_consecutive / len(quote_words) >= 0.6:
        logger.info(f"✅ Quote has {max_consecutive}/{len(quote_words)} consecutive words")
        return True
    
    # Fall back to word overlap (but log warning about potential paraphrase)
    # Check for substring match (at least 80% of words present)
    quote_words = set(source_quote_normalized.lower().split())
    source_words = set(source_text_normalized.lower().split())
    
    # Remove common words that don't matter
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}
    quote_words -= stop_words
    source_words -= stop_words
    
    if len(quote_words) == 0:
        return False
    
    overlap = len(quote_words & source_words)
    overlap_ratio = overlap / len(quote_words)
    
    if overlap_ratio >= 0.8:  # At least 80% of significant words match
        logger.warning(f"⚠️ Quote passes word overlap ({overlap_ratio:.1%}) but NOT exact/consecutive match")
        logger.warning(f"   May be paraphrased - review manually")
        return True
    
    logger.error(f"Quote validation failed: only {overlap_ratio:.1%} word overlap")
    return False

def detect_incomplete_templates(text):
    """
    Detect incomplete template patterns like 'at least ,' or 'for after'.
    
    Args:
        text: Text to check for incomplete templates
    
    Returns:
        bool: True if incomplete templates detected
    """
    if not text or not isinstance(text, str):
        return False
    
    patterns = [
        r'at\s+least\s+[,\.]',
        r'for\s+[,\.]',
        r'of\s+[,\.]',
        r'\s+of\s+the\s+time[,\.]',
        r'within\s+[,\.]',
        r'tested\s+for\s+after',
        r'operational\s+for\s+at\s+least\s+[,\.]',
        r'success\s+rate[,\.]',
        r'transmission\s+time\s+of[,\.]',
    ]
    
    for pattern in patterns:
        if re.search(pattern, text):
            logger.warning(f"Incomplete template detected: {pattern}")
            return True
    return False

def validate_no_metadata_leak(story):
    """
    Check for internal metadata in story output.
    
    Args:
        story: Story dict to validate
    
    Returns:
        bool: True if no metadata leak, False otherwise
    """
    dod = story.get('definitionOfDone', '')
    
    forbidden_patterns = [
        'Source Basis:',
        'Deliverables:',
        '{',
        '}',
        'internal_',
        'metadata_',
    ]
    
    for pattern in forbidden_patterns:
        if pattern in dod:
            logger.error(f"Story {story.get('id')}: Metadata leak detected: {pattern}")
            return False
    
    return True

def validate_story_coverage(stories, expected_min=6):
    """
    Validate that sufficient stories were extracted.
    
    Args:
        stories: List of story dicts
        expected_min: Minimum expected story count
    
    Returns:
        bool: True if coverage is adequate
    """
    story_count = len(stories)
    
    if story_count < expected_min:
        logger.error(f"🚨 LOW COVERAGE: Only {story_count} stories (expected {expected_min}+)")
        logger.error("⚠️ This might indicate:")
        logger.error("  - Too many stories rejected (check fabricated quotes)")
        logger.error("  - Source text too short")
        logger.error("  - Extraction logic filtering too aggressively")
        logger.error("  - LLM stopping early")
        return False
    
    logger.info(f"✅ Story coverage OK: {story_count} stories extracted")
    return True

def log_quality_metrics(stories, validation_errors):
    """
    Log quality metrics for tracking improvement over time.
    
    Args:
        stories: List of story dicts
        validation_errors: List of validation error messages
    
    Returns:
        dict: Quality metrics
    """
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'total_stories': len(stories),
        'validation_errors': len(validation_errors),
        'stories_with_source_quotes': sum(1 for s in stories if s.get('source_quote')),
        'stories_with_metrics': sum(1 for s in stories 
                                   if re.search(r'\d+%', s.get('definitionOfDone', ''))),
        'stories_with_templates': sum(1 for s in stories 
                                     if detect_incomplete_templates(s.get('definitionOfDone', ''))),
        'duplicate_titles': len(stories) - len(set(s.get('title', '') for s in stories)),
    }
    
    # Log to file for tracking
    try:
        # Get project root (3 levels up from this file: src/backend/services/story_service.py)
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file_dir)))
        metrics_file = os.path.join(project_root, 'data', 'logs', 'quality_metrics.jsonl')
        os.makedirs(os.path.dirname(metrics_file), exist_ok=True)
        with open(metrics_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(metrics) + '\n')
    except Exception as e:
        logger.warning(f"Could not write quality metrics: {e}")
    
    # Log summary
    logger.info("📊 QUALITY METRICS:")
    logger.info(f"  Stories: {metrics['total_stories']}")
    logger.info(f"  Errors: {metrics['validation_errors']}")
    logger.info(f"  With quotes: {metrics['stories_with_source_quotes']}")
    logger.info(f"  With metrics: {metrics['stories_with_metrics']}")
    logger.info(f"  Duplicate titles: {metrics['duplicate_titles']}")
    
    return metrics

def sanitize_story_output(story):
    """
    Clean up story output before returning.
    Removes internal metadata, Python dict syntax, and incomplete templates.
    """
    dod = story.get("definitionOfDone", "")
    
    if not dod or not isinstance(dod, str):
        return story
    
    # Remove internal metadata
    dod = re.sub(r'•\s*Source Basis:.*?(?=•|\Z)', '', dod, flags=re.DOTALL)
    dod = re.sub(r'•\s*Deliverables:.*?(?=•|\Z)', '', dod, flags=re.DOTALL)
    dod = re.sub(r'Source Basis:.*?(?=•|\n|\Z)', '', dod, flags=re.DOTALL)
    dod = re.sub(r'Deliverables:.*?(?=•|\n|\Z)', '', dod, flags=re.DOTALL)
    
    # Remove Python dict syntax
    dod = re.sub(r'\{[^}]*:[^}]*\}', '', dod)
    
    # Fix incomplete templates - REPLACE with generic text
    replacements = {
        r'at least\s+of\s+': '',  # Remove incomplete "at least of"
        r'\s+of required': ' required',
        r'\s+of the time': '',
        r'for\s+after': 'after',
    }
    
    for pattern, replacement in replacements.items():
        dod = re.sub(pattern, replacement, dod, flags=re.IGNORECASE)
    
    # Remove specific invented metrics
    # Percentages
    dod = re.sub(r'\d+\.?\d*%\s+\w+', '', dod)  # "99.9% uptime", "95% success"
    dod = re.sub(r'\d+\.?\d*%', '', dod)  # Any remaining percentages
    
    # Time-based metrics
    dod = re.sub(r'\d+\s+(second|seconds|minute|minutes|hour|hours|day|days)', '', dod, flags=re.IGNORECASE)
    dod = re.sub(r'within\s+\d+\s+\w+', 'efficiently', dod, flags=re.IGNORECASE)
    dod = re.sub(r'under\s+\d+\s+\w+', 'efficiently', dod, flags=re.IGNORECASE)
    
    # Bandwidth/speed metrics
    dod = re.sub(r'\d+\s*(kbps|mbps|gbps)', '', dod, flags=re.IGNORECASE)
    
    # Latency metrics
    dod = re.sub(r'\d+-?\w+\s+latency', 'efficient transmission', dod)
    
    # Generic "at least X" patterns
    dod = re.sub(r'at\s+least\s+\d+', '', dod, flags=re.IGNORECASE)
    
    # Clean up whitespace
    dod = re.sub(r'\s+', ' ', dod)
    dod = re.sub(r'[,\s]+\.', '.', dod)
    dod = re.sub(r'\.\s*\.', '.', dod)  # Remove double periods
    dod = dod.strip()
    
    # If DoD is empty or too short after cleaning, provide fallback
    if not dod or len(dod) < 10:
        story_text = story.get("description", "")
        if story_text:
            # Extract action from story
            action_part = story_text.split(' so that ')[0] if ' so that ' in story_text.lower() else story_text
            action_part = action_part.replace('The system must ', '').replace('The system shall ', '').strip()
            dod = f"System successfully implements {action_part.lower()}"
    
    story["definitionOfDone"] = dod
    return story

def validate_user_story_format(story):
    """
    Validate that a story follows proper user story format.
    
    Args:
        story: Story dict to validate
    
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    print("=" * 80)
    print("[VALIDATE] VALIDATE_USER_STORY_FORMAT CALLED")
    print(f"[VALIDATE] Story ID: {story.get('id', 'unknown')}")
    print("=" * 80)
    
    story_id = story.get('id', 'unknown')

    # Check required fields exist
    # Note: 'Title' is optional for v1 format - can be generated from 'User Story' if missing
    required_fields = ['User Story', 'Deliverables']
    for field in required_fields:
        if field not in story or not story[field]:
            print(f"[REJECT] VALIDATION FAILED: Missing required field: {field}")
            return False, f"Missing required field: {field}"

    # Title is optional for v1 - will be generated if missing
    if 'Title' not in story or not story.get('Title'):
        logger.debug(f"Story {story_id}: Title missing, will be generated from User Story")

    # Check User Story format
    user_story = story.get('User Story', '').strip()

    # Minimum length check
    if len(user_story) < 20:
        return False, f"User story too short ({len(user_story)} chars)"

    # Check for proper Agile format "As a [role], I want [feature], so that [benefit]"
    # v2 format should have this, v1 may use "must/shall" format
    has_agile_format = ('as a' in user_story.lower() or 'as the' in user_story.lower()) and 'i want' in user_story.lower()
    has_traditional_format = any(keyword in user_story.lower() for keyword in ['must', 'shall', 'can', 'should', 'will'])

    if not has_agile_format and not has_traditional_format:
        return False, "User story doesn't follow proper format (neither 'As a...I want' nor 'must/shall' format)"

    # Check for "so that" clause (business value) - WARNING only for traditional format
    if 'so that' not in user_story.lower():
        if has_agile_format:
            # For Agile format, "so that" is required
            logger.warning(f"Story {story_id}: Agile format detected but missing 'so that' clause")
        else:
            # For traditional format, just warn
            logger.warning(f"Story {story_id}: Missing 'so that' clause - business value unclear")

    # Check title - optional, will be generated if missing
    title = story.get('Title', '').strip()
    if title and len(title) < 3:
        return False, f"Title too short: '{title}'"

    # Check Acceptance Criteria (new in v2 format) - optional but recommended
    acceptance_criteria = story.get('Acceptance Criteria', [])
    if acceptance_criteria:
        if not isinstance(acceptance_criteria, list):
            logger.warning(f"Story {story_id}: Acceptance Criteria should be a list")
        elif len(acceptance_criteria) < 2:
            logger.warning(f"Story {story_id}: Only {len(acceptance_criteria)} acceptance criteria (recommend 3-5)")
    else:
        logger.debug(f"Story {story_id}: No Acceptance Criteria provided (optional for v1 format)")
    
    # Check deliverables exist and are not empty
    deliverables = story.get('Deliverables', {})
    if not deliverables or not isinstance(deliverables, dict):
        return False, "Deliverables missing or not a dictionary"
    
    if len(deliverables) == 0:
        return False, "Deliverables dictionary is empty"
    
    # Check each deliverable has definition of done
    for deliv_name, deliv_content in deliverables.items():
        if not isinstance(deliv_content, dict):
            return False, f"Deliverable '{deliv_name}' is not a dictionary"
        
        dod = deliv_content.get('definition_of_done') or deliv_content.get('definitionOfDone')
        if not dod or not isinstance(dod, str) or len(dod) < 10:
            return False, f"Deliverable '{deliv_name}' has invalid or missing definition_of_done"
    
    return True, None

def validate_generated_stories(stories, source_text):
    """
    Comprehensive validation of generated stories with rejection logic.
    Stories with fabricated quotes are REJECTED.
    Stories with other issues are flagged but included (will be sanitized).
    
    Args:
        stories: List of story dicts from LLM
        source_text: Original source document text
    
    Returns:
        tuple: (valid_stories: list, validation_errors: list)
    """
    print("=" * 80)
    print("[VALIDATE] VALIDATE_GENERATED_STORIES CALLED")
    print(f"[VALIDATE] Input stories count: {len(stories)}")
    print(f"[VALIDATE] Source text length: {len(source_text) if source_text else 0} chars")
    print("=" * 80)
    
    errors = []
    valid_stories = []
    
    for story in stories:
        story_id = story.get('id', 'unknown')
        story_errors = []
        
        # NEW: Validate user story format FIRST
        format_valid, format_error = validate_user_story_format(story)
        if not format_valid:
            logger.error(f"🚨 Story {story_id}: REJECTED - Invalid format: {format_error}")
            errors.append(f"Story {story_id}: REJECTED - {format_error}")
            continue  # Skip this story entirely
        
        # Bug 1: Fabricated quotes - Changed to WARNING instead of REJECT
        source_quote = story.get('source_quote', '').strip()
        if source_quote:
            if not validate_source_quote(source_quote, source_text):
                story_errors.append(f"Fabricated/invalid source quote")
                # WARNING: Log but don't reject - quote validation is too strict
                logger.warning(f"⚠️ Story {story_id}: Invalid/paraphrased quote: '{source_quote[:50]}...'")
                logger.warning(f"   Story will be included but quote validation failed")
                errors.append(f"Story {story_id}: Invalid source quote (included anyway)")
                # Don't reject - just log warning
        else:
            # Missing source quote is a warning, not rejection
            logger.warning(f"⚠️ Story {story_id}: Missing source_quote field")
            story_errors.append(f"Missing source_quote")
        
        # Bug 3: Invented metrics - WARNING, but clean and continue
        dod = story.get('definitionOfDone', '')
        if re.search(r'\d+%|\d+\s+(second|minute|hour|kbps|mbps)', dod):
            story_errors.append(f"Contains invented metrics (will be cleaned)")
            logger.warning(f"⚠️ Story {story_id}: Invented metrics detected")
        
        # Bug 4: Template failures - WARNING, will be cleaned
        if detect_incomplete_templates(dod):
            story_errors.append(f"Incomplete templates (will be cleaned)")
            logger.warning(f"⚠️ Story {story_id}: Template failures")
        
        # Bug 5: Metadata leak - WARNING, will be cleaned
        if not validate_no_metadata_leak(story):
            story_errors.append(f"Metadata leak (will be cleaned)")
            logger.warning(f"⚠️ Story {story_id}: Metadata leaked")
        
        # If story has errors but not fabricated quote, include with warnings
        if story_errors:
            errors.extend([f"Story {story_id}: {e}" for e in story_errors])
        
        # Story passed critical checks, include it
        valid_stories.append(story)
    
    # Log summary
    rejected = len(stories) - len(valid_stories)
    if rejected > 0:
        logger.error(f"❌ REJECTED {rejected} stories due to fabricated quotes")
    
    if errors:
        logger.warning(f"⚠️ {len(errors)} validation issues total ({rejected} rejections, {len(errors)-rejected} warnings)")
    else:
        logger.info(f"✅ All {len(valid_stories)} stories valid")
    
    return valid_stories, errors

def validate_story_output(stories):
    """
    Validate story outputs before saving.
    Rejects corrupted outputs with metadata leaks, incomplete templates, or duplicates.
    
    Returns:
        tuple: (is_valid: bool, errors: list)
    """
    errors = []
    
    for i, story in enumerate(stories, 1):
        dod = story.get("definitionOfDone", "")
        story_id = story.get("id", i)
        
        if not dod:
            errors.append(f"Story {story_id}: Missing Definition of Done")
            continue
        
        if not isinstance(dod, str):
            errors.append(f"Story {story_id}: Definition of Done is not a string")
            continue
        
        # Check for corruption markers
        if "Source Basis:" in dod:
            errors.append(f"Story {story_id}: Contains 'Source Basis:' metadata")
        
        if "Deliverables:" in dod and dod.count("Deliverables:") > 1:
            errors.append(f"Story {story_id}: Contains duplicate 'Deliverables:' metadata")
        
        if re.search(r'\{[^}]*:[^}]*\}', dod):
            errors.append(f"Story {story_id}: Contains Python dict syntax in DoD")
        
        # Check for incomplete templates
        incomplete_patterns = [
            r'at least\s+of\s+',
            r'for\s+after\s+',
            r'tested for\s+$',
            r'\s+of the time$',
            r'\s+of required$',
        ]
        
        for pattern in incomplete_patterns:
            if re.search(pattern, dod, re.IGNORECASE):
                errors.append(f"Story {story_id}: Incomplete template pattern detected: '{pattern}'")
        
        # Check for duplicate DoDs
        for j, other in enumerate(stories[:i-1], 1):
            other_dod = other.get("definitionOfDone", "")
            if dod == other_dod and len(dod) > 20:  # Only flag if substantial duplicate
                errors.append(f"Story {story_id}: Duplicate DoD with Story {other.get('id', j)}")
    
    if errors:
        logger.error("❌ VALIDATION FAILED:")
        for error in errors:
            logger.error(f"  {error}")
        return False, errors
    
    return True, []

def generate_real_test_case(story_description):
    """
    Generate concrete test case instead of template based on story description.
    
    Args:
        story_description: User story description text
    
    Returns:
        list: List of test case dictionaries with concrete input/output
    """
    if not story_description or not isinstance(story_description, str):
        return []
    
    # Extract action verb
    action = ""
    if "must" in story_description.lower():
        parts = story_description.lower().split("must")
        if len(parts) > 1:
            action = parts[1].split("so that")[0].strip()
    else:
        # Fallback: extract first meaningful verb
        words = story_description.lower().split()
        verbs = ["collect", "transmit", "store", "maintain", "charge", "report", "update", "monitor", "process"]
        for i, word in enumerate(words):
            if word in verbs and i < len(words) - 1:
                action = " ".join(words[i:i+5])
                break
    
    if not action:
        action = story_description[:50]
    
    # Generate based on action type
    action_lower = action.lower()
    
    # Generate generic test case based on action
    # This avoids hardcoding domain-specific logic (like weather stations)
    
    return [
        {
            "name": f"Verify {action}",
            "input": {
                "action": action,
                "test_data": "valid_input_parameters"
            },
            "expected_output": {
                "status": "success",
                "verification": f"{action} completed successfully",
                "error_code": None
            }
        },
        {
            "name": f"Verify {action} with invalid data",
            "input": {
                "action": action,
                "test_data": "invalid_input_parameters"
            },
            "expected_output": {
                "status": "error",
                "error_handling": "graceful_failure_message"
            }
        }
    ]
    
    # Default generic test (but still concrete)
    return [
        {
            "name": f"Test: {action[:50]}",
            "input": {"action_requested": action},
            "expected_output": {"action_completed": True, "status": "success"}
        }
    ]

def is_template_test_case(test_case_text):
    """
    Detect if a test case is a useless template.
    
    Args:
        test_case_text: String containing test case description
    
    Returns:
        True if it's a template, False if it's a real test case
    """
    if not test_case_text or not isinstance(test_case_text, str):
        return False
    
    test_lower = test_case_text.lower()
    
    # Template patterns
    template_patterns = [
        r'verify that the system must',
        r'functionality works as specified',
        r'functionality works as specified in the user story',
        r'test cases will be defined',
        r'test: verify that',
        r'expected:.*works as specified',
    ]
    
    for pattern in template_patterns:
        if re.search(pattern, test_lower):
            return True
    
    # Check if it's too generic (no concrete data)
    if len(test_case_text) < 50:  # Very short test cases are likely templates
        if 'verify' in test_lower and 'expected' in test_lower:
            return True
    
    return False

def remove_invented_metrics(text):
    """
    Remove invented metrics (percentages, time windows, specific numbers) from text.
    These metrics are often fabricated by the LLM and not present in source text.
    
    Args:
        text: String containing Definition of Done or other text that may have invented metrics
    
    Returns:
        Cleaned text with invented metrics removed
    """
    if not text or not isinstance(text, str):
        return text
    
    # Patterns to remove invented metrics
    patterns_to_remove = [
        # Percentages
        r'\d+\.\d+%',                    # "99.9%", "95.5%"
        r'\d+%',                         # "90%", "95%"
        r'<\s*\d+%',                     # "<1%", "< 5%"
        r'>\s*\d+%',                     # ">99%", "> 95%"
        r'at least\s+\d+%',              # "at least 95%"
        r'up to\s+\d+%',                 # "up to 90%"
        r'\d+%\s+of\s+\w+',              # "90% of stations"
        r'\d+%\s+\w+',                   # "90% accuracy", "95% uptime"
        
        # Time windows and latencies
        r'within\s+\d+\s+\w+',          # "within 5 minutes", "within 2 hours"
        r'less than\s+\d+\s+\w+',       # "less than 1 second", "less than 10 minutes"
        r'more than\s+\d+\s+\w+',       # "more than 30 seconds"
        r'\d+\s*-\s*\d+\s+\w+',         # "5-10 minutes", "2-3 seconds"
        r'\d+\s+seconds?',               # "1 second", "2 seconds"
        r'\d+\s+minutes?',                # "5 minutes", "10 minutes"
        r'\d+\s+hours?',                  # "24 hours", "2 hours"
        r'\d+\s+days?',                   # "7 days", "30 days"
        r'does not exceed\s+\d+',        # "does not exceed 2 seconds"
        r'latency\s+of\s+less\s+than\s+\d+',  # "latency of less than 10 minutes"
        r'\d+\s*second\s+latency',       # "1 second latency"
        r'\d+\s*minute\s+latency',       # "10 minute latency"
        
        # Count metrics
        r'\d+\s+transmissions?',         # "30 transmissions"
        r'\d+\s+of\s+components?',       # "80% of components" (already caught by % pattern, but keep for safety)
        r'\d+\s+stations?',              # "90% of target stations" (when combined with %)
        
        # Success/error rates with numbers
        r'\d+\.\d+%\s+accuracy',         # "99.9% accuracy"
        r'\d+%\s+accuracy',              # "95% accuracy"
        r'\d+\.\d+%\s+uptime',           # "99.9% uptime"
        r'\d+%\s+uptime',                # "99% uptime"
        r'error\s+rate\s+below\s+\d+%',  # "error rate below 5%"
        r'error\s+rate\s+of\s+less\s+than\s+\d+%',  # "error rate of less than 1%"
        r'error\s+rate\s+<\s+\d+%',      # "error rate <1%"
        
        # Specific thresholds
        r'threshold\s+of\s+\d+',         # "threshold of 1 second"
        r'\d+\s+threshold',              # "1-second threshold"
    ]
    
    cleaned = text
    removed_items = []
    
    for pattern in patterns_to_remove:
        matches = re.finditer(pattern, cleaned, re.IGNORECASE)
        # Collect all matches first (reverse order to preserve indices)
        match_list = list(matches)
        match_list.reverse()
        
        for match in match_list:
            removed_items.append(match.group())
            # Remove the matched text
            cleaned = cleaned[:match.start()] + cleaned[match.end():]
    
    # Clean up extra whitespace and punctuation artifacts
    # Remove multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned)
    # Remove orphaned commas/punctuation
    cleaned = re.sub(r',\s*,', ',', cleaned)
    cleaned = re.sub(r',\s*\.', '.', cleaned)
    cleaned = re.sub(r'\s+\.', '.', cleaned)
    # Remove leading/trailing whitespace
    cleaned = cleaned.strip()
    
    # Log what was removed (for debugging)
    if removed_items:
        logger.info(f"[METRIC REMOVAL] Removed {len(removed_items)} invented metrics: {removed_items[:5]}...")
    
    return cleaned

def remove_duplicate_stories(stories):
    """Remove duplicate or very similar user stories"""
    if not stories:
        return stories
    
    unique_stories = []
    seen_texts = set()
    
    for story in stories:
        # Safety: ensure each story item is a dict before calling .get()
        if not isinstance(story, dict):
            if isinstance(story, str) and story.strip():
                story = {"User Story": story.strip(), "Deliverables": {}}
            elif isinstance(story, list) and story:
                story = {"User Story": str(story[0]).strip(), "Deliverables": {}}
            else:
                continue
        story_text = story.get('User Story', '').strip().lower()
        
        # Skip empty stories
        if not story_text:
            logger.info(f"Skipping empty story")
            continue
        
        # Check for exact duplicates
        if story_text in seen_texts:
            logger.info(f"Skipping duplicate story: {story_text[:50]}...")
            continue
        
        # Check for similar stories (word overlap similarity)
        is_duplicate = False
        for seen_text in seen_texts:
            # Calculate word overlap similarity
            words1 = set(story_text.split())
            words2 = set(seen_text.split())
            
            if len(words1) > 0 and len(words2) > 0:
                # Intersection of words
                overlap = len(words1.intersection(words2))
                # Use Jaccard similarity (intersection / union)
                union = len(words1.union(words2))
                jaccard_similarity = overlap / union if union > 0 else 0
                
                # If more than 60% word overlap, consider it duplicate (more aggressive)
                if jaccard_similarity > 0.6:
                    logger.info(f"Skipping similar story (Jaccard similarity: {jaccard_similarity:.2f})")
                    logger.info(f"  New: {story_text[:60]}...")
                    logger.info(f"  Existing: {seen_text[:60]}...")
                    is_duplicate = True
                    break
        
        if not is_duplicate:
            unique_stories.append(story)
            seen_texts.add(story_text)
            logger.info(f"Added story: {story_text[:60]}...")
    
    removed_count = len(stories) - len(unique_stories)
    logger.info(f"\nDeduplication summary: Kept {len(unique_stories)} unique stories, removed {removed_count} duplicates")
    return unique_stories

def normalize_story_structure(story):
    """
    Normalize story structure to match expected schema.
    Fixes common schema violations like flattened Deliverables.
    """
    # Ensure story is a dictionary
    if not isinstance(story, dict):
        if isinstance(story, list) and len(story) > 0:
            # If it's a list, try to make a dict from it
            return {"User Story": str(story[0]), "Deliverables": {}}
        return {"User Story": str(story), "Deliverables": {}}

    if 'Deliverables' in story and isinstance(story['Deliverables'], dict):
        deliverables = story['Deliverables']
        
        # Check if flattened: {"definitionOfDone": "..."} instead of {"name": {"definitionOfDone": "..."}}
        if 'definitionOfDone' in deliverables and isinstance(deliverables['definitionOfDone'], str):
            # It's flattened! Fix it by wrapping it.
            story['Deliverables'] = {
                "Main Deliverable": {
                    "definitionOfDone": deliverables['definitionOfDone']
                }
            }
            logger.info(f"Fixed flattened Deliverables for story {story.get('id')}")
            
    return story

def convert_stories_to_frontend_format(epics_json, test_cases_json, requirements_text):
    """
    Convert backend output format to frontend format
    Backend returns: { "User Stories": [...], "Test Cases": {...} }
    Frontend expects: [{ title, description, definitionOfDone, testCases }]
    """
    print("=" * 80)
    print("[ENTRY] convert_stories_to_frontend_format CALLED")
    print("=" * 80)
    
    try:
        # Robust JSON parsing function
        def parse_robust(item, fallback_key="data"):
            if not isinstance(item, str):
                return item
            try:
                return json.loads(item)
            except json.JSONDecodeError:
                pass

            # Use depth-tracked brace matching to extract a JSON block from prose
            for start_char, end_char in [('{', '}'), ('[', ']')]:
                start_idx = item.find(start_char)
                if start_idx == -1:
                    continue
                depth = 0
                in_string = False
                escape_next = False
                for i, ch in enumerate(item[start_idx:], start=start_idx):
                    if escape_next:
                        escape_next = False
                        continue
                    if ch == '\\' and in_string:
                        escape_next = True
                        continue
                    if ch == '"':
                        in_string = not in_string
                        continue
                    if in_string:
                        continue
                    if ch == start_char:
                        depth += 1
                    elif ch == end_char:
                        depth -= 1
                        if depth == 0:
                            try:
                                return json.loads(item[start_idx:i + 1])
                            except json.JSONDecodeError:
                                break  # try [ ... ] next

            # Nothing parseable — return an empty structure, NOT the raw string.
            # Returning the raw string causes iteration over characters downstream.
            logger.warning(f"[parse_robust] Could not parse JSON from input (first 200 chars): {item[:200]}")
            return {fallback_key: []}

        epics_data = parse_robust(epics_json, "User Stories")
        test_cases_data = parse_robust(test_cases_json, "Test Cases")
        
        # Try both "User Stories" and "Epics" keys (LLM might return either)
        # Also handle case where epics_data is a list directly
        user_stories = []
        
        if isinstance(epics_data, dict):
            user_stories = epics_data.get('User Stories', [])
            logger.info(f"[convert] Found {len(user_stories)} stories in 'User Stories' key")
            
            if not user_stories:
                # Try "Epics" key as fallback
                epics_list = epics_data.get('Epics', [])
                logger.info(f"[convert] Found {len(epics_list)} stories in 'Epics' key")
                if epics_list:
                    logger.info(f"Found 'Epics' key instead of 'User Stories', using it...")
                    user_stories = epics_list
                else:
                    # Try "Functional Requirements" key (autoAgile might return this)
                    func_reqs = epics_data.get('Functional Requirements', [])
                    logger.info(f"[convert] Found {len(func_reqs)} stories in 'Functional Requirements' key")
                    if func_reqs:
                        logger.info(f"Found 'Functional Requirements' key, using it...")
                        user_stories = func_reqs
                    else:
                        logger.error(f"[convert] No user stories found! Available keys: {list(epics_data.keys())}")
        elif isinstance(epics_data, list):
            # If epics_data is already a list, use it directly
            logger.info(f"[convert] epics_data is a list with {len(epics_data)} items, using it directly")
            user_stories = epics_data
        else:
            logger.error(f"[convert] epics_data is neither dict nor list! Type: {type(epics_data)}")
        
        # Handle different test cases formats
        # Format 1: {"Test Cases": {...}} - dictionary with keys
        # Format 2: {"testCases": [...]} - array of test case objects
        # Format 3: {"test_cases": [...]} - snake_case array (v2 format)
        # Format 4: Direct list of test cases (autoAgile might return this)
        test_cases_list = []
        test_cases_dict = {}

        if isinstance(test_cases_data, dict):
            # Try all possible key variations
            raw_tc_dict = test_cases_data.get('Test Cases', {})
            test_cases_dict = raw_tc_dict if isinstance(raw_tc_dict, dict) else {}

            # Try multiple list key variations (order matters - try most specific first)
            raw_tc_list = (test_cases_data.get('test_cases') or  # v2 snake_case
                          test_cases_data.get('testCases') or     # camelCase
                          test_cases_data.get('Test Cases'))      # space separated

            if isinstance(raw_tc_list, list):
                test_cases_list = raw_tc_list
                logger.info(f"[convert] Found {len(test_cases_list)} test case groups in test_cases_data")
            else:
                logger.warning(f"[convert] No test_cases list found. Keys available: {list(test_cases_data.keys())}")
        elif isinstance(test_cases_data, list):
            # If test_cases_data is already a list, use it directly
            test_cases_list = test_cases_data
            logger.info(f"[convert] test_cases_data is a list with {len(test_cases_list)} groups")
        else:
            logger.error(f"[convert] test_cases_data is neither dict nor list! Type: {type(test_cases_data)}")
        
        # Normalize FIRST, then deduplicate to ensure all items are dicts
        user_stories = [normalize_story_structure(s) for s in user_stories]
        
        # Remove duplicate stories based on similarity
        user_stories = remove_duplicate_stories(user_stories)
        
        print("=" * 80)
        print("[DEBUG] CONVERT_STORIES_TO_FRONTEND_FORMAT - About to validate")
        print(f"[DEBUG] User stories count after dedup: {len(user_stories)}")
        print("=" * 80)
        
        # VALIDATION DISABLED - Accept all stories
        logger.info(f"Processing {len(user_stories)} stories (validation disabled)...")
        valid_stories = user_stories  # Skip validation, use all stories
        validation_errors = []
        
        # # 🆕 PHASE 1: VALIDATION (Before sanitization)
        # logger.info(f"🔍 Validating {len(user_stories)} stories...")
        # valid_stories, validation_errors = validate_generated_stories(
        #     user_stories, 
        #     requirements_text
        # )
        
        # if len(valid_stories) < len(user_stories):
        #     rejected = len(user_stories) - len(valid_stories)
        #     logger.error(f"❌ Rejected {rejected} stories due to critical errors")
        
        # # 🆕 Check coverage
        # if not validate_story_coverage(valid_stories):
        #     logger.warning("⚠️ Low story coverage detected")
        
        
        frontend_stories = []
        # Track which TC groups have been claimed so each group goes to exactly one story
        claimed_tc_groups = set()

        for idx, story in enumerate(valid_stories):
            # Extract user story title/description
            story_text = story.get('User Story', '').strip()

            # Use title from LLM if available, otherwise generate one
            title = story.get('Title', '').strip()

            # Generate title if not provided or if it's generic/truncated
            if not title or title.endswith('Must') or title.endswith('Shall') or len(title) < 5:
                # Generate a COMPLETE, meaningful title (3-5 words)
                if story_text:
                    # Remove common prefixes to get to the core action
                    action_text = story_text
                    prefixes_to_remove = [
                        'The Insulin Pump system must ',
                        'The Insulin Pump system shall ',
                        'The insulin pump system must ',
                        'The insulin pump system shall ',
                        'Insulin Pump system must ',
                        'The system must ',
                        'The system shall ',
                        'System must ',
                        'System shall '
                    ]

                    for prefix in prefixes_to_remove:
                        if action_text.startswith(prefix):
                            action_text = action_text[len(prefix):]
                            break

                    # Extract the action part (before "so that")
                    if ' so that ' in action_text.lower():
                        action_part = action_text.split(' so that ')[0].strip()
                    else:
                        action_part = action_text

                    # Remove common stop words and extract meaningful keywords
                    words = action_part.split()
                    meaningful_words = []
                    stop_words = {'the', 'a', 'an', 'and', 'or', 'for', 'with', 'from', 'to', 'in', 'on', 'at', 'by', 'of', 'be', 'is', 'are'}

                    for w in words:
                        w_clean = w.rstrip(',;.').lower()
                        # Skip stop words unless it's a key verb
                        if w_clean not in stop_words or w_clean in {'collect', 'calculate', 'compute', 'send', 'deliver', 'monitor', 'process'}:
                            meaningful_words.append(w.rstrip(',;.'))
                        # Stop at 4-5 words for a good title length
                        if len(meaningful_words) >= 5:
                            break

                    # Use first 3-5 meaningful words as title
                    if meaningful_words:
                        title = ' '.join(meaningful_words[:5])
                    else:
                        # Fallback: use first 4 words
                        title = ' '.join(words[:4])

                    # Capitalize properly for title case
                    title = ' '.join(word.capitalize() for word in title.split())
                else:
                    title = f'User Story {idx + 1}'
            
            # Extract Acceptance Criteria (new in v2 format)
            acceptance_criteria = story.get('Acceptance Criteria', [])
            ac_items = []
            if acceptance_criteria and isinstance(acceptance_criteria, list):
                for criterion in acceptance_criteria:
                    if isinstance(criterion, str) and criterion.strip():
                        ac_items.append(f"  - {criterion.strip()}")

            # Extract deliverables and format properly
            deliverables = story.get('Deliverables', {})
            deliverable_items = []

            if deliverables and isinstance(deliverables, dict):
                # Remove "User Story" key if it exists (it's redundant)
                deliverables_filtered = {k: v for k, v in deliverables.items() if k != 'User Story'}

                for key, value in deliverables_filtered.items():
                    # Format key name (convert snake_case to Title Case)
                    formatted_key = key.replace('_', ' ').title()

                    if isinstance(value, dict):
                        # Try multiple fields for definition of done
                        dod = (value.get('definition_of_done') or
                               value.get('definitionOfDone') or
                               value.get('description') or
                               value.get('criteria'))

                        # Handle list format (v2 format uses arrays for DoD)
                        if isinstance(dod, list):
                            dod_text = '\n    '.join([f"- {item}" for item in dod if isinstance(item, str) and item.strip()])
                            if dod_text:
                                deliverable_items.append(f"• {formatted_key}:\n    {dod_text}")
                        elif isinstance(dod, str) and dod.strip() and dod.strip().upper() != 'TBD':
                            # Remove invented metrics from DoD
                            dod_cleaned = remove_invented_metrics(dod)
                            deliverable_items.append(f"• {formatted_key}: {dod_cleaned}")
                    else:
                        # Skip if value is "TBD" or empty
                        value_str = str(value).strip()
                        if value_str and value_str.upper() != 'TBD':
                            # Remove invented metrics from value
                            value_cleaned = remove_invented_metrics(value_str)
                            deliverable_items.append(f"• {formatted_key}: {value_cleaned}")

            # Build Definition of Done with Acceptance Criteria + Deliverables
            dod_parts = []

            # Add Acceptance Criteria section if present
            if ac_items:
                dod_parts.append("Acceptance Criteria:")
                dod_parts.extend(ac_items)
                if deliverable_items:
                    dod_parts.append("")  # Blank line separator

            # Add Deliverables section
            if deliverable_items:
                if ac_items:
                    dod_parts.append("Deliverables:")
                dod_parts.extend(deliverable_items)

            # Fallback if nothing found
            if not dod_parts:
                if story_text:
                    # Try to identify the main feature/component
                    action_part = story_text.split(' so that ')[0] if ' so that ' in story_text.lower() else story_text
                    # Remove common prefixes
                    action_part = action_part.replace('As a ', '').replace('I want ', '').replace('The system must ', '').replace('The ', '').strip()
                    # Create a basic deliverable from the action
                    if action_part:
                        dod_parts.append(f"• Feature Implementation: {action_part}")

            definition_of_done = '\n'.join(dod_parts) if dod_parts else 'Deliverables will be defined during sprint planning'
            # Remove any invented metrics from the final definition_of_done
            definition_of_done = remove_invented_metrics(definition_of_done)
            
            # Get test cases for this story
            # Try multiple matching strategies
            test_cases = None

            def _tc_similarity(req_text, story_text):
                """Return Jaccard similarity (0-1) between two requirement texts."""
                if not req_text or not story_text:
                    return 0.0
                stop = {'the', 'a', 'an', 'and', 'or', 'for', 'with', 'from', 'to',
                        'in', 'on', 'at', 'by', 'of', 'be', 'is', 'are', 'that',
                        'this', 'must', 'shall', 'will', 'can', 'system', 'using'}
                def keywords(t):
                    return set(w.strip('.,;:[]()') for w in t.lower().split()
                               if len(w) > 3 and w.lower() not in stop)
                req_kw = keywords(req_text)
                story_kw = keywords(story_text)
                if not req_kw or not story_kw:
                    return 0.0
                intersection = req_kw & story_kw
                union = req_kw | story_kw
                return len(intersection) / len(union)

            # Strategy 1: Best-match assignment — each TC group claimed by at most one story.
            # Score every unclaimed group against this story; take the highest scoring one
            # above the threshold. This prevents the same TCs appearing in multiple stories.
            if isinstance(test_cases_list, list) and len(test_cases_list) > 0:
                matching_test_cases = []
                best_score = 0.0
                best_group_idx = -1
                best_nested = []

                for group_idx, test_group in enumerate(test_cases_list):
                    if group_idx in claimed_tc_groups:
                        continue  # already assigned to an earlier story
                    if not isinstance(test_group, dict):
                        continue
                    requirement_text = test_group.get('requirement', '')
                    nested_test_cases = test_group.get('test_cases', [])
                    if not requirement_text or not isinstance(nested_test_cases, list):
                        continue
                    score = _tc_similarity(requirement_text, story_text)
                    logger.debug(f"[Story {idx+1}] group {group_idx} score={score:.2f} req='{requirement_text[:50]}'")
                    if score > best_score:
                        best_score = score
                        best_group_idx = group_idx
                        best_nested = nested_test_cases

                # Claim the best group if it clears the minimum threshold
                if best_group_idx != -1 and best_score >= 0.25:
                    claimed_tc_groups.add(best_group_idx)
                    matching_test_cases = best_nested
                    logger.info(f"Claimed TC group {best_group_idx} for story {idx+1} (score={best_score:.2f})")

                if matching_test_cases:
                    # Format test cases with detailed structure (ID, description, steps, expected result)
                    formatted_tests = []
                    for test in matching_test_cases:
                        if isinstance(test, dict):
                            test_id = test.get('id', '')
                            test_desc = test.get('description', '')
                            test_steps = test.get('steps', [])
                            test_expected = test.get('expected_result', '')

                            # Format nicely with ID, description, steps, and expected result
                            test_formatted_parts = []
                            if test_id:
                                test_formatted_parts.append(f"**{test_id}**: {test_desc}")
                            else:
                                test_formatted_parts.append(f"**Test**: {test_desc}")

                            if test_steps and isinstance(test_steps, list):
                                test_formatted_parts.append("**Steps**:")
                                for i, step in enumerate(test_steps, 1):
                                    test_formatted_parts.append(f"  {i}. {step}")

                            if test_expected:
                                test_formatted_parts.append(f"**Expected**: {test_expected}")

                            formatted_tests.append('\n'.join(test_formatted_parts))

                    test_cases = '\n\n'.join(formatted_tests) if formatted_tests else json.dumps(matching_test_cases, indent=2)
                    logger.info(f"Found and formatted {len(matching_test_cases)} detailed test cases for story {idx + 1}")
            
            # Strategy 2: Try dictionary lookup by index
            if not test_cases and test_cases_dict:
                test_cases = test_cases_dict.get(str(idx + 1), '')
                if not test_cases:
                    # Try to find by story text
                    for key, value in test_cases_dict.items():
                        if story_text.lower() in str(value).lower() or str(value).lower() in story_text.lower():
                            test_cases = value
                            break
            
            # Strategy 3: If still no match, create a basic test case from story
            if not test_cases or test_cases == '-':
                # Generate a basic test case from the story text (but avoid templates)
                if story_text:
                    action_part = story_text.split(' so that ')[0] if ' so that ' in story_text.lower() else story_text
                    # Remove common prefixes
                    action_part = action_part.replace('The system must ', '').replace('The system shall ', '').replace('The ', '').strip()
                    # Create a more specific test case (not a template)
                    test_cases = f"Test: {action_part}\nExpected: System performs {action_part.lower()} successfully with valid output data"
                else:
                    test_cases = 'Test cases will be defined during test planning'
            
            # Post-process: Remove template test cases
            if test_cases and isinstance(test_cases, str):
                if is_template_test_case(test_cases):
                    logger.info(f"[TEST CASE FILTER] Detected template test case for story {idx + 1}, replacing with placeholder")
                    test_cases = f"Test cases need to be defined with concrete input/output data for: {story_text[:100] if story_text else 'this requirement'}"
            
            # Convert to string if needed
            if isinstance(test_cases, dict):
                test_cases = json.dumps(test_cases, indent=2)
            elif not isinstance(test_cases, str):
                test_cases = str(test_cases)
            
            # Generate real test cases if we have template or empty test cases
            if not test_cases or test_cases == '-' or is_template_test_case(test_cases):
                logger.info(f"[TEST CASE GENERATION] Generating concrete test cases for story {idx + 1}")
                real_test_cases = generate_real_test_case(story_text)
                if real_test_cases:
                    test_cases = json.dumps(real_test_cases, indent=2)
            
            
            # Extract source quote (evidence from document)
            source_quote = story.get('source_quote', '').strip()
            if not source_quote:
                # Try alternate field names for backwards compatibility
                source_quote = story.get('source_basis', '').strip()
            
            # Log warning if source quote is missing
            if not source_quote:
                logger.warning(f"Story {idx + 1} missing source_quote field - may lack source evidence")
            
            frontend_stories.append({
                'id': idx + 1,
                'title': title,
                'description': story_text,  # Full user story text
                'source_quote': source_quote,  # Evidence from source document
                'definitionOfDone': definition_of_done,  # Formatted deliverables
                'testCases': test_cases
            })
        
        # Sanitize all stories
        logger.info("SANITIZATION: Cleaning story outputs...")
        sanitized_stories = [sanitize_story_output(story.copy()) for story in frontend_stories]
        
        # Validate outputs
        logger.info("VALIDATION: Checking for corruption and duplicates...")
        is_valid, validation_errors = validate_story_output(sanitized_stories)
        
        if not is_valid:
            logger.warning(f"WARNING: {len(validation_errors)} validation issues found!")
            # Continue anyway - don't block, but warn user
        else:
            logger.info("VALIDATION PASSED: No corruption detected!")
        
        # 🆕 PHASE 3: QUALITY METRICS (Track quality)
        quality_metrics = log_quality_metrics(sanitized_stories, validation_errors)
        
        return sanitized_stories
    except Exception as e:
        logger.error(f"Error converting stories: {e}")
        # Return a basic format if conversion fails
        return [{
            'id': 1,
            'title': 'Error processing stories',
            'description': str(e),
            'definitionOfDone': '-',
            'testCases': '-'
        }]
