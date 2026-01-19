"""
Output formatting and saving functionality for user stories.

This module handles saving generated stories, epics, and test cases to JSON files.
"""
import json
import os
import logging

logger = logging.getLogger(__name__)


def save_json_output(requirements, epics, test_cases, docx_path):
    """
    Save combined requirements, epics, and test cases to JSON output file.

    Args:
        requirements: Requirements text
        epics: JSON string of epics
        test_cases: JSON string of test cases
        docx_path: Path to the original document file

    Returns:
        Path to the saved output file
    """
    # Generate the output file name with the same base name as the input .docx file but with .txt extension
    base_name = os.path.basename(docx_path)     # Extracts the base name from the given file_path
    # Splits the base name into two parts: the name and the extension, returning only the name part
    output_file_name = os.path.splitext(base_name)[0] + '.txt'

    # Use absolute path relative to project root (not this file's location)
    # Get project root (3 levels up from this file: src/core_engine/output.py)
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_file_dir))
    output_dir = os.path.join(project_root, "data", "outputs")

    # Check if the directory exists, and if not, create it
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, mode=0o777, exist_ok=True)

    output_path = os.path.join(output_dir, output_file_name)
    
    # Parse epics and test cases
    try:
        data1 = json.loads(epics)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse epics JSON: {e}")
        data1 = {"User Stories": []}
    
    try:
        data2 = json.loads(test_cases)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse test_cases JSON: {e}")
        data2 = {"testCases": []}
    
    # Try to parse requirements as JSON first
    req_json_data = {}
    try:
        # Check if requirements is already JSON
        if requirements.strip().startswith('{'):
            req_json_data = json.loads(requirements)
        else:
            # Try to extract JSON from the text
            import re
            json_match = re.search(r'\{.*\}', requirements, re.DOTALL)
            if json_match:
                req_json_data = json.loads(json_match.group())
            else:
                # Fallback: parse as simple text format
                lines = requirements.strip().split('\n')
                if lines:
                    key = lines[0].strip().rstrip(':')
                    values = [line.strip() for line in lines[1:] if line.strip()]
                    req_json_data = {key: values}
    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"Failed to parse requirements, using empty structure: {e}")
        req_json_data = {"requirements": []}
    
    # Combine all data - ensure we have proper structure
    final_data = {}
    
    # Add requirements (ensure it's an array)
    if "requirements" in req_json_data:
        final_data["requirements"] = req_json_data["requirements"]
    elif isinstance(req_json_data, dict) and len(req_json_data) == 1:
        # If it's a single key dict, check if it's requirements
        key = list(req_json_data.keys())[0]
        if "requirement" in key.lower():
            final_data["requirements"] = req_json_data[key] if isinstance(req_json_data[key], list) else [req_json_data[key]]
        else:
            final_data["requirements"] = []
    else:
        final_data["requirements"] = []
    
    # Add user stories
    if "User Stories" in data1:
        final_data["User Stories"] = data1["User Stories"]
    elif "Epics" in data1:
        # Convert Epics to User Stories format
        final_data["User Stories"] = data1["Epics"]
    else:
        final_data["User Stories"] = []
    
    # Add test cases
    if "testCases" in data2:
        final_data["testCases"] = data2["testCases"]
    elif "Test Cases" in data2:
        final_data["testCases"] = data2["Test Cases"]
    else:
        final_data["testCases"] = []
    
    # Convert to JSON format
    final_json = json.dumps(final_data, indent=4)

    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(final_json)
    
    logger.info(f"Output saved to: {output_path}")
    return output_path
