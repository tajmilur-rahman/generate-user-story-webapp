"""
Standalone CLI interface for autoAgile user story generation.

Usage:
    python -m core_engine.cli <document.docx> [model_name]

Example:
    python -m core_engine.cli tests/docs/test.docx llama3.2:latest
"""
import json
import sys
import os

from .prompts import (
    extract_text_from_docx,
    refine_doc,
    extract_functionarity,
    refine_requirements,
    extract_epics,
    get_epics,
    generate_test_cases,
    rat
)
from .llm_factory import get_chat_model
from .output import save_json_output


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python -m core_engine.cli <document.docx> [model_name]")
        print("Example: python -m core_engine.cli tests/docs/test.docx llama3.2:latest")
        sys.exit(1)
    
    DOC = sys.argv[1]
    temp = float(os.environ.get('LLM_TEMPERATURE', '0.3'))
    
    # Get model name
    if len(sys.argv) > 2:
        Model = sys.argv[2]
    else:
        # Use default based on provider
        llm_provider = os.environ.get('LLM_PROVIDER', 'ollama').lower()
        if llm_provider == 'ollama':
            Model = os.environ.get('OLLAMA_MODEL', 'llama3.2:latest')
        else:
            Model = os.environ.get('OPENAI_MODEL', 'gpt-4-turbo')
    
    # Set mode
    mode = os.environ.get('MODE', 'prod')  # or 'debug'
    
    print(f"🤖 Model: {Model}")
    print(f"📊 LLM Provider: {os.environ.get('LLM_PROVIDER', 'ollama')}")
    print(f"🌡️  Temperature: {temp}")
    print(f"📄 Document: {DOC}")
    print(f"{'='*60}\n")
    
    try:
        # Initialize chat model
        chat = get_chat_model(temperature=temp, model_name=Model)
        
        # Extract text from document
        docx_path = DOC
        extracted_text = ""
        try:
            extracted_text = extract_text_from_docx(docx_path)
            if mode == "debug":
                print("Text extracted successfully:\n")
                print("=============================\n")
                print(extracted_text)
                print("=============================\n")
        except Exception as e:
            print(f"❌ Error extracting text: {str(e)}")
            sys.exit(1)
        
        # Generate requirements
        print("📝 Step 1: Extracting requirements...")
        requirements = rat(refine_doc, extract_functionarity, extracted_text, chat, mode)
        print(requirements)
        print()
        
        # Generate epics/user stories
        print("🎯 Step 2: Generating user stories...")
        deliverables = rat(refine_requirements, extract_epics, requirements, chat, mode)
        if mode == "debug":
            print(deliverables)
        epics = get_epics(deliverables, chat)
        print(epics)
        print()
        
        # Generate test cases
        print("🧪 Step 3: Generating test cases...")
        test_cases = rat(refine_requirements, generate_test_cases, requirements, chat, mode)
        print(test_cases)
        print()
        
        # Save output
        print("💾 Step 4: Saving output...")
        output_path = save_json_output(requirements, epics, test_cases, docx_path)
        print(f"✅ Complete! Output saved to: {output_path}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        if mode == "debug":
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
