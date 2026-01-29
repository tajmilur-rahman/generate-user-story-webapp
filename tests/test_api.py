import pytest
import json
import io
import sys
import os
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from backend.app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'ok'

def test_index_page(client):
    """Test frontend index page"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'User Story Automation' in response.data or b'html' in response.data

def test_stories_page(client):
    """Test frontend stories page"""
    response = client.get('/stories.html')
    assert response.status_code == 200

@patch('routes.api.rat')
@patch('routes.api.get_epics')
@patch('routes.api.validate_output')
@patch('routes.api.validate_requirements_completeness')
@patch('routes.api.save_json_output')
@patch('routes.api.ChatOllama')
def test_generate_stories(mock_ollama, mock_save, mock_validate_comp, mock_validate, mock_get_epics, mock_rat, client):
    """Test story generation endpoint with mocks"""
    # Mock LLM responses
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
    
    # Mock validation
    mock_validate.return_value = {'issues': []}
    mock_validate_comp.return_value = {'issues': []}
    
    # Mock save output
    mock_save.return_value = "dummy_output.json"
    
    # Mock file upload
    data = {
        'file': (io.BytesIO(b"dummy content"), 'test.txt'),
        'model': 'llama3.2'
    }
    
    # Force LLM_PROVIDER to be 'ollama' for this test
    with patch('routes.api.LLM_PROVIDER', 'ollama'):
        response = client.post('/api/generate-stories', data=data, content_type='multipart/form-data')
    
    # Check for error response to debug
    if response.status_code != 200:
        print(f"Error response: {response.data}")
        
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert len(data['stories']) == 1
    assert data['stories'][0]['title'] == 'Allow Login'

def test_generate_stories_no_file(client):
    """Test error when no file provided"""
    response = client.post('/api/generate-stories', data={})
    assert response.status_code == 400
