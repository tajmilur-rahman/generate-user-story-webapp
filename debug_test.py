import unittest
from unittest.mock import MagicMock, patch
import json
import io
import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

from app import create_app

def run_test():
    print("Initializing app...")
    app = create_app()
    app.config['TESTING'] = True
    client = app.test_client()
    
    print("Setting up mocks...")
    # Setup mocks manually
    with patch('routes.api.rat') as mock_rat, \
         patch('routes.api.get_epics') as mock_get_epics, \
         patch('routes.api.validate_output') as mock_validate, \
         patch('routes.api.validate_requirements_completeness') as mock_validate_comp, \
         patch('routes.api.save_json_output') as mock_save, \
         patch('routes.api.ChatOllama') as mock_ollama, \
         patch('routes.api.LLM_PROVIDER', 'ollama'):
         
        mock_rat.side_effect = ["Requirements text", "Deliverables text", "Test cases text"]
        mock_get_epics.return_value = json.dumps({
            "User Stories": [
                {
                    "User Story": "The system must allow login so that users can access their account",
                    "Deliverables": {"Login Form": "Standard login form"},
                    "Acceptance Criteria": ["User enters credentials", "System validates"]
                }
            ]
        })
        mock_validate.return_value = {'issues': []}
        mock_validate_comp.return_value = {'issues': []}
        
        data = {
            'file': (io.BytesIO(b"dummy content"), 'test.txt'),
            'model': 'llama3.2'
        }
        
        print("Sending request...")
        try:
            response = client.post('/api/generate-stories', data=data, content_type='multipart/form-data')
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.data.decode('utf-8')}")
        except Exception as e:
            print(f"EXCEPTION: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    run_test()
