
import os
import sys
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

# Mock Flask app context if needed or just import services
try:
    from backend.services.story_service import normalize_story_structure, validate_generated_stories, convert_stories_to_frontend_format
    
    # Mock data from debug log
    mock_epics_json = """
    {
      "User Stories": [
        {
          "id": 1,
          "Title": "Weather Station System",
          "User Story": "The system must collect weather data so that it can be processed and transmitted to other systems.",
          "Deliverables": {
            "definitionOfDone": "Clear criteria for collecting, processing, and transmitting weather data"
          },
          "source_quote": "Collects weather data, performs initial data processing, and transmits it to the data management system."
        }
      ]
    }
    """
    
    mock_requirements_text = """
    The weather station system is part of a larger weather information system that collects data from weather stations and makes it available for processing.
    Collects weather data, performs initial data processing, and transmits it to the data management system.
    """
    
    print("\n--- Verifying Pipeline ---")
    
    # 1. Parse
    epics_data = json.loads(mock_epics_json)
    stories = epics_data["User Stories"]
    print(f"1. Parsed {len(stories)} stories")
    
    # 2. Normalize
    normalized_stories = [normalize_story_structure(s) for s in stories]
    print("2. Normalized stories:")
    print(json.dumps(normalized_stories[0]['Deliverables'], indent=2))
    
    # 3. Validate
    print("\n3. Validating...")
    valid_stories, errors = validate_generated_stories(normalized_stories, mock_requirements_text)
    
    if errors:
        print("ERRORS FOUND:")
        for e in errors:
            print(f" - {e}")
    
    print(f"\nFinal Valid Stories: {len(valid_stories)}")
    
    if len(valid_stories) > 0:
        print("SUCCESS: Pipeline is working!")
    else:
        print("FAILURE: Validation rejected the story.")

except Exception as e:
    print(f"\nCRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()
