"""
LLM Factory for autoAgile
Supports OpenAI, Ollama, and Groq based on LLM_PROVIDER environment variable
"""
import os
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq

def get_chat_model(temperature=0.3, model_name=None):
    """
    Get chat model based on LLM_PROVIDER environment variable.
    
    Args:
        temperature: Temperature for the model (default: 0.3)
        model_name: Optional model name override
    
    Returns:
        Chat model instance (ChatOpenAI, ChatOllama, or ChatGroq)
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
    elif llm_provider == 'groq':
        api_key = os.environ.get('GROQ_API_KEY', '').strip()
        if not api_key:
            raise ValueError("Groq API key not found. Set GROQ_API_KEY in environment.")
        model = model_name or "llama-3.3-70b-versatile"
        return ChatGroq(
            model=model,
            temperature=temperature,
            api_key=api_key
        )
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {llm_provider}. Use 'ollama', 'openai', or 'groq'.")
