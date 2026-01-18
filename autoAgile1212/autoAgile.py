"""Main module."""
import json
import sys
import os
from utils.prompts import *
from utils.llm_factory import get_chat_model
from save_output import *

DOC = sys.argv[1]
temp = float(os.environ.get('LLM_TEMPERATURE', '0.3'))
Model = ""
prod = "prod"
debug = "debug"
mode = prod
try:
    Model = sys.argv[2] 
except:
    # Use default based on provider
    llm_provider = os.environ.get('LLM_PROVIDER', 'ollama').lower()
    if llm_provider == 'ollama':
        Model = os.environ.get('OLLAMA_MODEL', 'llama3.2:latest')
    else:
        Model = os.environ.get('OPENAI_MODEL', 'gpt-4-turbo')

print(f"model is {Model}")
print(f"LLM provider: {os.environ.get('LLM_PROVIDER', 'ollama')}")

if __name__ == "__main__":
    chat = get_chat_model(temperature=temp, model_name=Model)
    # Replace 'your_file.docx' with the path to your DOCX file
    docx_path = DOC
    extracted_text = ""
    try:
        extracted_text = extract_text_from_docx(docx_path)
        if mode == debug:
            print("Text extracted successfully:\n")
            print("=============================\n")
            print(extracted_text)
            print("=============================\n")
    except Exception as e:
        print("Error extracting text:", str(e))
    requirements = rat(refine_doc, extract_functionarity, extracted_text, chat, mode)
    print(requirements)
    deliverables = rat(refine_requirements, extract_epics, requirements, chat, mode)
    if mode == debug:
        print(deliverables)
    epics = get_epics(deliverables, chat)
    test_cases = rat(refine_requirements, generate_test_cases, requirements, chat,mode)
    #test_cases is in json text already
    print(epics)
    print(test_cases)

    # save the output into a file
    save_json_output(requirements, epics, test_cases,docx_path)


    
