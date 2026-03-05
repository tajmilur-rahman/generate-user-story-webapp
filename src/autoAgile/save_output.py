import json
import os

def save_json_output(requirements, epics, test_cases, docx_path):
    # Generate the output file name with the same base name as the input .docx file but with .txt extension
    base_name = os.path.basename(docx_path)     # Extracts the base name from the given file_path
    # Splits the base name into two parts: the name and the extension, returning only the name part
    output_file_name = os.path.splitext(base_name)[0] + '.txt'
    

    # Use project-relative path - updated to use data/outputs
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    output_dir = os.path.join(project_root, "data", "outputs") 


# Check if the directory exists, and if not, create it
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, mode=0o777, exist_ok=True)


    output_path = os.path.join(output_dir, output_file_name)
    

    # Helper to extract JSON if it's wrapped in conversational text
    def parse_robust(item):
        if not isinstance(item, str):
            return item
        try:
            return json.loads(item)
        except json.JSONDecodeError:
            # Try to find JSON block { ... } or [ ... ]
            try:
                start_dict = item.find('{')
                end_dict = item.rfind('}')
                if start_dict != -1 and end_dict != -1:
                    json_str = item[start_dict:end_dict+1]
                    return json.loads(json_str)
            except:
                pass
            return {"raw_text": item}

    # Handle both string JSON and dict objects
    data1 = parse_robust(epics)
    data2 = parse_robust(test_cases)
    
    # Ensure they are dicts before merging
    if not isinstance(data1, dict):
        data1 = {"epics": data1}
    if not isinstance(data2, dict):
        data2 = {"test_cases": data2}
        
    combined_data = {**data1, **data2}


    


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
    #parse jsondata into a python dictionary
    req_json_data = json.loads(req_json)

    #Merge req json with combined data
    req_json_data.update(combined_data)

    # Convert combined_data back to JSON format
    final_json = json.dumps(req_json_data, indent=4)

    with open(output_path, 'w') as file:
        file.write(final_json)
    
    # Return the output path for the API
    return output_path