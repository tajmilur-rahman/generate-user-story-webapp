import pytest
import json
import io
from unittest.mock import patch, MagicMock
from app import create_app
from autoAgile.tests.test_doc_resources import doc_text_raw

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@patch('routes.api.rat')
@patch('routes.api.get_epics')
@patch('routes.api.validate_output')
@patch('routes.api.validate_requirements_completeness')
@patch('routes.api.save_json_output')
@patch('routes.api.ChatOllama')
def test_generate_erie_stories(mock_ollama, mock_save, mock_validate_comp, mock_validate, mock_get_epics, mock_rat, client):
    """Test story generation with Erie Insurance document content"""
    
    # Mock LLM responses
    mock_rat.side_effect = ["Requirements text", "Deliverables text", "Test cases text"]
    
    # Mock get_epics to return what we expect from the new prompt structure
    mock_get_epics.return_value = json.dumps({
        "User Stories": [
            {
                "Title": "Agent Search Functionality",
                "User Story": "The system must allow users to search for agents by name so that they can quickly find contact details.",
                "source_basis": "Agent search is the primary feature...",
                "Deliverables": {
                    "Search UI": {
                        "definition_of_done": "Search bar is visible on landing page and accepts text input."
                    }
                }
            }
        ]
    })
    
    # Mock validation
    mock_validate.return_value = {'issues': []}
    mock_validate_comp.return_value = {'issues': []}
    mock_save.return_value = "erie_output.json"
    
    # Create a mock file with Erie Insurance content
    data = {
        'file': (io.BytesIO(doc_text_raw.encode('utf-8')), 'erie_handbook.txt'),
        'model': 'llama3.2'
    }
    
    # Force LLM_PROVIDER to be 'ollama'
    with patch('routes.api.LLM_PROVIDER', 'ollama'):
        response = client.post('/api/generate-stories', data=data, content_type='multipart/form-data')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    print(f"DEBUG DATA: {json.dumps(data, indent=2)}")
    assert data['success'] is True
    assert len(data['stories']) == 1
    
    story = data['stories'][0]
    # Verify structure matches frontend expectations
    assert 'title' in story
    assert 'description' in story
    assert 'definitionOfDone' in story
    assert 'testCases' in story
    
    # Verify content
    assert story['title'] == "Agent Search Functionality"
    assert "search for agents" in story['description']
    assert "Search UI" in story['definitionOfDone']
