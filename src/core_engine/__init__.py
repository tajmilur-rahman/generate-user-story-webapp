"""
Core Engine - User Story Generation
Based on autoAgile1212 - The proven, working implementation

This module contains the core business logic for generating user stories from documents.
Independent of the backend (Flask) and frontend, allowing for standalone use.

Main modules:
- prompts: LLM prompts and story generation functions (from autoAgile)
- llm_factory: LLM initialization factory (OpenAI, Ollama, Groq)
- output: Output formatting and saving
- validation: Basic output validation
"""

__author__ = """Yuecai"""
__email__ = 'zhuyuecai@gmail.com'
__version__ = '0.1.0'

from .prompts import (
    extract_text_from_docx,
    clean_doc,
    summarize_doc,
    refine_doc,
    extract_list,
    extract_functionarity,
    refine_requirements,
    extract_epics,
    refine_epics,
    get_epics,
    generate_test_cases,
    rat,
    compare_answer,
    self_consistency,
    rank_answer,
    c_o_t,
)

from .llm_factory import (
    get_chat_model,
)

from .output import (
    save_json_output,
)

from .validation import (
    validate_output,
    validate_requirements_completeness,
    print_validation_report,
)

__all__ = [
    # Prompts (autoAgile core functions)
    'extract_text_from_docx',
    'clean_doc',
    'summarize_doc',
    'refine_doc',
    'extract_list',
    'extract_functionarity',
    'refine_requirements',
    'extract_epics',
    'refine_epics',
    'get_epics',
    'generate_test_cases',
    'rat',
    'compare_answer',
    'self_consistency',
    'rank_answer',
    'c_o_t',
    # LLM Factory
    'get_chat_model',
    # Output
    'save_json_output',
    # Validation
    'validate_output',
    'validate_requirements_completeness',
    'print_validation_report',
]
