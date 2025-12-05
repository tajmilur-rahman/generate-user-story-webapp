
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Mock environment if needed
os.environ['LLM_PROVIDER'] = 'ollama'

try:
    from core_engine.prompts import extract_epics
    import json

    # Mock chat model
    chat = ChatOllama(model="llama3.2:latest", temperature=0)

    # Sample requirements text
    requirements_text = """
    The system must allow users to log in securely.
    The Weather Station shall collect temperature data every 5 minutes.
    The system must transmit data to the central server.
    """

    print("--- Testing extract_epics ---")
    try:
        result = extract_epics(requirements_text, chat, mode="debug")
        print("\nRaw Result:")
        print(result)
        
        print("\nValidating JSON parsing:")
        parsed = json.loads(result)
        print(json.dumps(parsed, indent=2))
        
        if "User Stories" in parsed and isinstance(parsed["User Stories"], list):
            print(f"\nSUCCESS: Found {len(parsed['User Stories'])} stories.")
        else:
            print("\nFAILURE: 'User Stories' key missing or not a list.")
            
    except Exception as e:
        print(f"\nERROR calling extract_epics: {e}")
        import traceback
        traceback.print_exc()

except ImportError as e:
    print(f"ImportError: {e}")
    # checking path
    print(f"Current Path: {sys.path}")
