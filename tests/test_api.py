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
    # /api/generate-stories gained @login_required after these tests were
    # written, so an unauthenticated request now redirects (302) instead of
    # reaching the handler. LOGIN_DISABLED is Flask-Login's supported way to
    # exercise a protected view without standing up a session.
    app.config['LOGIN_DISABLED'] = True
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

# The handler's collaborators changed in the src/ restructure: validate_output,
# validate_requirements_completeness and ChatOllama are no longer imported by
# this module, and the LLM now comes from get_chat_model rather than being
# constructed inline. Patch what the handler actually calls.
@patch('backend.routes.api.save_json_output')
@patch('backend.routes.api.generate_test_cases_v2')
@patch('backend.routes.api.get_epics_v2')
@patch('backend.routes.api.extract_epics_v2')
@patch('backend.routes.api.rat')
@patch('backend.routes.api.get_chat_model')
def test_generate_stories(mock_chat, mock_rat, mock_extract_epics, mock_get_epics,
                          mock_test_cases, mock_save, client):
    """Story generation endpoint returns converted stories with the LLM mocked."""
    mock_chat.return_value = MagicMock()
    mock_rat.return_value = "REQ-001: The system must allow login"
    mock_extract_epics.return_value = json.dumps({"Epics": []})
    mock_get_epics.return_value = json.dumps({
        "User Stories": [
            {
                "User Story": "The system must allow login so that users can access their account",
                "Deliverables": {"Login Form": "Standard login form"},
                "Acceptance Criteria": ["User enters credentials", "System validates"]
            }
        ]
    })
    mock_test_cases.return_value = json.dumps({"test_cases": []})
    mock_save.return_value = "dummy_output.json"

    data = {
        'file': (io.BytesIO(b"The system must allow login."), 'test.txt'),
        'model': 'llama3.2'
    }

    with patch('backend.routes.api.LLM_PROVIDER', 'ollama'):
        response = client.post('/api/generate-stories', data=data,
                               content_type='multipart/form-data')

    if response.status_code != 200:
        print(f"Error response: {response.data}")

    assert response.status_code == 200
    payload = json.loads(response.data)
    assert payload['success'] is True
    assert len(payload['stories']) == 1


def test_generate_stories_no_file(client):
    """Test error when no file provided"""
    response = client.post('/api/generate-stories', data={})
    assert response.status_code == 400
