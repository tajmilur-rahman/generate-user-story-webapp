"""
Output formatting and saving functionality for user stories.
"""
import json
import os

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
    base_name = os.path.basename(docx_path)
    output_file_name = os.path.splitext(base_name)[0] + '.txt'
    
    # Use project-relative path - go up from core_engine to project root
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_file_dir))
    output_dir = os.path.join(project_root, "data", "outputs")
    
    # Check if the directory exists, and if not, create it
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, mode=0o777, exist_ok=True)
    
    output_path = os.path.join(output_dir, output_file_name)
    
    try:
        data1 = json.loads(epics)
    except json.JSONDecodeError:
        data1 = {"User Stories": []}
    
    try:
        data2 = json.loads(test_cases)
    except json.JSONDecodeError:
        data2 = {"testCases": []}
    
    combined_data = {**data1, **data2}
    
    # Parse requirements
    lines = requirements.strip().split('\n')
    
    # Use the first line as the key
    key = lines[0].strip().rstrip(':')
    
    # Collect the rest of the lines into a list
    values = [line.strip() for line in lines[1:]]
    
    # Create a dictionary with the key and values list
    data0 = {
        key: values
    }
    
    # Convert to JSON format
    req_json = json.dumps(data0, indent=4)
    req_json_data = json.loads(req_json)
    
    # Merge req json with combined data
    req_json_data.update(combined_data)
    
    # Convert combined_data back to JSON format
    final_json = json.dumps(req_json_data, indent=4)
    
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(final_json)
    
    print(f"Output saved to: {output_path}")
    return output_path
