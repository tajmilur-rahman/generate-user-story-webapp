"""
LLM Factory for autoAgile1212
Supports both OpenAI and Ollama based on LLM_PROVIDER environment variable
"""
import os
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama

def get_chat_model(temperature=0.3, model_name=None):
    """
    Get chat model based on LLM_PROVIDER environment variable.
    
    Args:
        temperature: Temperature for the model (default: 0.3)
        model_name: Optional model name override
    
    Returns:
        Chat model instance (ChatOpenAI or ChatOllama)
    """
    llm_provider = os.environ.get('LLM_PROVIDER', 'ollama').lower()
    
    if llm_provider == 'ollama':
        base_url = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
        model = model_name or os.environ.get('OLLAMA_MODEL', 'llama3.2:latest')
        return ChatOllama(
            model=model,
            base_url=base_url,
            temperature=temperature
        )
    elif llm_provider == 'openai':
        api_key = os.environ.get('OPENAI_API_KEY', '') or os.environ.get('auth_key', '')
        if not api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY or auth_key in environment.")
        model = model_name or os.environ.get('OPENAI_MODEL', 'gpt-4-turbo')
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            openai_api_key=api_key
        )
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {llm_provider}. Use 'ollama' or 'openai'.")
