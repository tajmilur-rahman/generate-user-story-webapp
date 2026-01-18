# autoAgile1212 Integration

## Overview

The `autoAgile1212` folder has been integrated into the project and configured to work with both OpenAI and Ollama LLM providers.

## Location

The integrated folder is located at:
```
user-story-automation/
└── autoAgile1212/
    ├── autoAgile.py          # Main entry point
    ├── save_output.py        # Output saving functionality
    ├── utils/
    │   ├── prompts.py        # All prompts (unchanged)
    │   ├── llm_factory.py    # NEW: LLM provider factory
    │   └── utils.py
    └── tests/                 # Test files and documents
```

## Key Changes

### 1. ✅ LLM Factory (`utils/llm_factory.py`)

Created a new factory function that supports both OpenAI and Ollama:

```python
from autoAgile1212.utils.llm_factory import get_chat_model

# Works with both OpenAI and Ollama
chat = get_chat_model(temperature=0.3, model_name=None)
```

**Configuration via environment variables:**
- `LLM_PROVIDER`: `'ollama'` (default) or `'openai'`
- `OLLAMA_BASE_URL`: Default `'http://localhost:11434'`
- `OLLAMA_MODEL`: Default `'llama3.2:latest'`
- `OPENAI_API_KEY` or `auth_key`: For OpenAI
- `LLM_TEMPERATURE`: Default `0.3`

### 2. ✅ Updated `autoAgile.py`

Modified to use the LLM factory instead of hardcoded ChatOpenAI:

```python
from utils.llm_factory import get_chat_model

chat = get_chat_model(temperature=temp, model_name=Model)
```

### 3. ✅ Updated Prompt Functions

Modified `compare_answer`, `rank_answer`, and `rat` functions to work with both OpenAI and Ollama using LangChain's LCEL (LangChain Expression Language) with fallback to LLMChain for compatibility.

### 4. ✅ Fixed Output Path

Updated `save_output.py` to use project-relative paths instead of hardcoded relative paths.

## Prompts - UNCHANGED

**All prompts in `utils/prompts.py` remain exactly as they were** - no modifications to the prompt text or structure.

## Usage

### Standalone Usage

```bash
# Set environment variables
export LLM_PROVIDER=ollama  # or 'openai'
export OLLAMA_MODEL=llama3.2:latest

# Run autoAgile1212
cd autoAgile1212
python autoAgile.py path/to/document.docx [model_name]
```

### Integration with Main Project

The autoAgile1212 functions can be imported and used in the main project:

```python
from autoAgile1212.utils.prompts import (
    extract_text_from_docx,
    refine_doc,
    extract_functionarity,
    extract_epics,
    get_epics,
    generate_test_cases,
    refine_requirements,
    rat
)
from autoAgile1212.utils.llm_factory import get_chat_model

# Initialize chat model (works with Ollama or OpenAI)
chat = get_chat_model(temperature=0.3)

# Use the functions
requirements = rat(refine_doc, extract_functionarity, doc_text, chat, "prod")
deliverables = rat(refine_requirements, extract_epics, requirements, chat, "prod")
epics = get_epics(deliverables, chat)
test_cases = rat(refine_requirements, generate_test_cases, requirements, chat, "prod")
```

## Configuration

### For Ollama (Default)

```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:latest
LLM_TEMPERATURE=0.3
```

### For OpenAI

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=your_api_key_here
# OR
auth_key=your_api_key_here
LLM_TEMPERATURE=0.3
```

## Features

- ✅ **Ollama Support**: Works with local Ollama models
- ✅ **OpenAI Support**: Works with OpenAI API (backward compatible)
- ✅ **Prompts Unchanged**: All original prompts preserved
- ✅ **Backward Compatible**: Existing code using OpenAI still works
- ✅ **Environment-Based**: Configuration via environment variables

## Testing

Test the integration:

```python
from autoAgile1212.utils.llm_factory import get_chat_model

# Test Ollama
chat = get_chat_model(temperature=0.3)
print(f"Chat model type: {type(chat)}")
```

## Notes

- The prompts are **exactly as they were** - no modifications
- LLM provider selection is automatic based on `LLM_PROVIDER` env var
- All functions accept a `chat` parameter, so they work with any LangChain-compatible LLM
- The integration maintains backward compatibility with OpenAI-based workflows
