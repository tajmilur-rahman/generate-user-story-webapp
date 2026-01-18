"""
Core Engine - User Story Generation Logic

This module contains the core business logic for generating user stories from documents.
It is independent of the backend (Flask) and frontend, allowing for independent development.

Main modules:
- prompts: LLM prompts and story generation functions
- validation: Output validation logic
- output: Output formatting and saving
"""

from .prompts import (
    extract_text_from_docx,
    refine_doc,
    extract_functionarity,
    extract_epics,
    generate_test_cases,
    refine_requirements,
    rat,
    clean_json_response,
    safe_json_loads,
)

from .validation import (
    validate_output,
    validate_requirements_completeness,
    print_validation_report,
)

from .output import (
    save_json_output,
)

__all__ = [
    # Prompts
    'extract_text_from_docx',
    'refine_doc',
    'extract_functionarity',
    'extract_epics',
    'generate_test_cases',
    'refine_requirements',
    'rat',
    'clean_json_response',
    'safe_json_loads',
    # Validation
    'validate_output',
    'validate_requirements_completeness',
    'print_validation_report',
    # Output
    'save_json_output',
]
