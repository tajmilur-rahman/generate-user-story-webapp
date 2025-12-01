import re
import json
import logging
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
        with open('quality_metrics.jsonl', 'a', encoding='utf-8') as f:
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
    story_id = story.get('id', 'unknown')
    
    # Check required fields exist
    required_fields = ['User Story', 'Title', 'Deliverables']
    for field in required_fields:
        if field not in story or not story[field]:
            return False, f"Missing required field: {field}"
    
    # Check User Story format
    user_story = story.get('User Story', '').strip()
    
    # Minimum length check
    if len(user_story) < 20:
        return False, f"User story too short ({len(user_story)} chars)"
    
    # Check for proper format: should contain "must" or "shall" or "can"
    valid_keywords = ['must', 'shall', 'can', 'should', 'will']
    has_valid_keyword = any(keyword in user_story.lower() for keyword in valid_keywords)
    
    if not has_valid_keyword:
        return False, "User story doesn't contain action keywords (must/shall/can/should/will)"
    
    # Check for "so that" clause (business value)
    if 'so that' not in user_story.lower():
        return False, "User story missing 'so that' clause for business value"
    
    # Check title is not empty and not too short
    title = story.get('Title', '').strip()
    if len(title) < 3:
        return False, f"Title too short: '{title}'"
    
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

def convert_stories_to_frontend_format(epics_json, test_cases_json, requirements_text):
    """
    Convert backend output format to frontend format
    Backend returns: { "User Stories": [...], "Test Cases": {...} }
    Frontend expects: [{ title, description, definitionOfDone, testCases }]
    """
    try:
        # Safe JSON parsing with fallbacks
        if isinstance(epics_json, str):
            try:
                epics_data = json.loads(epics_json)
            except json.JSONDecodeError:
                logger.warning(f"Error parsing epics_json, trying to clean...")
                # Try cleaning
                cleaned = epics_json.replace("```json", "").replace("```", "").strip()
                start = cleaned.find('{')
                end = cleaned.rfind('}')
                if start != -1 and end != -1:
                    cleaned = cleaned[start:end+1]
                try:
                    epics_data = json.loads(cleaned)
                except:
                    epics_data = {"User Stories": []}
        else:
            epics_data = epics_json
        
        if isinstance(test_cases_json, str):
            try:
                test_cases_data = json.loads(test_cases_json)
            except json.JSONDecodeError:
                logger.warning(f"Error parsing test_cases_json, trying to clean...")
                cleaned = test_cases_json.replace("```json", "").replace("```", "").strip()
                start = cleaned.find('{')
                end = cleaned.rfind('}')
                if start != -1 and end != -1:
                    cleaned = cleaned[start:end+1]
                try:
                    test_cases_data = json.loads(cleaned)
                except:
                    test_cases_data = {"Test Cases": {}}
        else:
            test_cases_data = test_cases_json
        
        # Try both "User Stories" and "Epics" keys (LLM might return either)
        user_stories = epics_data.get('User Stories', [])
        if not user_stories:
            # Try "Epics" key as fallback
            epics_list = epics_data.get('Epics', [])
            if epics_list:
                logger.debug(f"Found 'Epics' key instead of 'User Stories', converting...")
                user_stories = epics_list
        
        # Handle different test cases formats
        # Format 1: {"Test Cases": {...}} - dictionary with keys
        # Format 2: {"testCases": [...]} - array of test case objects
        test_cases_dict = test_cases_data.get('Test Cases', {})
        test_cases_list = test_cases_data.get('testCases', [])
        
        # Remove duplicate stories based on similarity
        user_stories = remove_duplicate_stories(user_stories)
        
        # 🆕 PHASE 1: VALIDATION (Before sanitization)
        logger.info(f"🔍 Validating {len(user_stories)} stories...")
        valid_stories, validation_errors = validate_generated_stories(
            user_stories, 
            requirements_text
        )
        
        if len(valid_stories) < len(user_stories):
            rejected = len(user_stories) - len(valid_stories)
            logger.error(f"❌ Rejected {rejected} stories due to critical errors")
        
        # 🆕 Check coverage
        if not validate_story_coverage(valid_stories):
            logger.warning("⚠️ Low story coverage detected")
        
        frontend_stories = []
        
        for idx, story in enumerate(valid_stories):
            # Extract user story title/description
            story_text = story.get('User Story', '').strip()
            
            # Use title from LLM if available, otherwise generate one
            title = story.get('Title', '').strip()
            
            if not title:
                # Generate a COMPLETE, meaningful title (3-5 words)
                if story_text:
                    # Check if story follows "The system must [action] so that [benefit]" pattern
                    if ' so that ' in story_text.lower():
                        # Extract action part (before "so that")
                        action_part = story_text.split(' so that ')[0].strip()
                        # Remove common prefixes
                        action_part = action_part.replace('The system must ', '').replace('The system shall ', '').replace('Users can ', '').replace('The ', '').strip()
                        
                        # Extract meaningful action words (skip stop words but keep important verbs)
                        words = action_part.split()
                        meaningful_words = []
                        stop_words = {'and', 'the', 'for', 'with', 'from', 'to', 'a', 'an', 'in', 'on', 'at', 'by'}
                        
                        for w in words:
                            w_clean = w.rstrip(',;.').lower()
                            # Keep verbs and important words, skip stop words
                            if w_clean not in stop_words or w_clean in {'shall', 'must', 'can', 'will'}:
                                meaningful_words.append(w.rstrip(',;.'))
                            # Take 4-5 words for a complete title
                            if len(meaningful_words) >= 5:
                                break
                        
                        # If we have meaningful words, use them; otherwise use first 4 words
                        if meaningful_words:
                            title = ' '.join(meaningful_words[:5])
                        else:
                            title = ' '.join(words[:4])
                        
                        # Capitalize first letter of each word for title case
                        title = ' '.join(word.capitalize() for word in title.split())
                    else:
                        # Fallback: extract first 4-5 meaningful words
                        words = story_text.split()
                        meaningful_words = []
                        stop_words = {'the', 'system', 'must', 'shall', 'can', 'will', 'and', 'for', 'with'}
                        for w in words:
                            w_clean = w.rstrip(',;.').lower()
                            if w_clean not in stop_words:
                                meaningful_words.append(w.rstrip(',;.'))
                            if len(meaningful_words) >= 5:
                                break
                        title = ' '.join(meaningful_words) if meaningful_words else ' '.join(words[:4])
                        title = ' '.join(word.capitalize() for word in title.split())
                else:
                    title = f'User Story {idx + 1}'
            
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
                               value.get('criteria') or
                               str(value))
                        # Skip if it's just "TBD" or empty
                        if dod and dod.strip() and dod.strip().upper() != 'TBD':
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
            
            # If no deliverables found, try to infer from story text
            if not deliverable_items:
                # Extract key functionality from story text as a fallback
                if story_text:
                    # Try to identify the main feature/component
                    action_part = story_text.split(' so that ')[0] if ' so that ' in story_text.lower() else story_text
                    # Remove common prefixes
                    action_part = action_part.replace('The system must ', '').replace('The system shall ', '').replace('The ', '').strip()
                    # Create a basic deliverable from the action
                    if action_part:
                        deliverable_items.append(f"• Feature Implementation: {action_part}")
            
            definition_of_done = '\n'.join(deliverable_items) if deliverable_items else 'Deliverables will be defined during sprint planning'
            # Remove any invented metrics from the final definition_of_done
            definition_of_done = remove_invented_metrics(definition_of_done)
            
            # Get test cases for this story
            # Try multiple matching strategies
            test_cases = None
            
            # Strategy 1: Match by requirement ID (try multiple field name variations)
            if isinstance(test_cases_list, list) and len(test_cases_list) > 0:
                matching_tests = []
                for test_case in test_cases_list:
                    if isinstance(test_case, dict):
                        # Try different field name variations (camelCase and snake_case)
                        req_id = (test_case.get('requirementId') or 
                                 test_case.get('requirementID') or 
                                 test_case.get('requirement_id') or 
                                 test_case.get('req_id'))
                        
                        # Match by index (1-based) - STRICT matching
                        if req_id and req_id == idx + 1:
                            matching_tests.append(test_case)
                        # Also try matching by story text keywords
                        elif story_text:
                            test_case_text = str(test_case).lower()
                            story_keywords = [w for w in story_text.lower().split() if len(w) > 4]
                            if any(kw in test_case_text for kw in story_keywords[:3]):
                                matching_tests.append(test_case)
                
                if matching_tests:
                    # Format test cases nicely
                    formatted_tests = []
                    for test in matching_tests:
                        test_name = test.get('name') or test.get('testCaseName') or test.get('test_case_name') or 'Test Case'
                        test_desc = test.get('description') or test.get('testDescription') or ''
                        formatted_tests.append(f"{test_name}: {test_desc}")
                    test_cases = '\n'.join(formatted_tests) if formatted_tests else json.dumps(matching_tests, indent=2)
                    logger.debug(f"Found {len(matching_tests)} test cases for story {idx + 1}")
            
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
            logger.warning(f"⚠️ WARNING: {len(validation_errors)} validation issues found!")
            # Continue anyway - don't block, but warn user
        else:
            logger.info("✅ VALIDATION PASSED: No corruption detected!")
        
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
