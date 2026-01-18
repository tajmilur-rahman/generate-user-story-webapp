# Architecture Separation Analysis

## Overview
This document analyzes the separation of concerns between the **Core Engine**, **Backend**, and **Frontend** components of the User Story Automation application.

## Current Architecture

### Directory Structure
```
user-story-automation/
├── src/
│   ├── core_engine/          # Core business logic (story generation)
│   │   ├── prompts.py        # LLM prompts and processing
│   │   └── validation.py     # Validation logic
│   ├── backend/              # Flask API server
│   │   ├── routes/           # API endpoints
│   │   ├── services/         # Business logic adapters
│   │   ├── models/           # Database models
│   │   └── llm/              # (Potential duplicate)
│   └── frontend/             # Web UI
│       ├── static/           # CSS, JS
│       └── templates/        # HTML
├── autoAgile/                # Legacy/duplicate core engine
└── ...
```

## Separation Analysis

### ✅ **Core Engine** (`src/core_engine/`)

**Status: ✅ WELL SEPARATED**

**Dependencies:**
- ✅ NO Flask dependencies
- ✅ NO backend dependencies  
- ✅ Only uses: `langchain`, `docx`, standard library
- ✅ Pure Python functions - can be used independently

**Exports:**
- `extract_text_from_docx()` - Document extraction
- `extract_epics()` - Epic/story generation
- `generate_test_cases()` - Test case generation
- `validate_output()` - Validation logic
- `rat()` - Refinement and thought process

**Can be developed independently:** ✅ YES

### ✅ **Backend** (`src/backend/`)

**Status: ✅ PROPERLY SEPARATED**

**Dependencies:**
- ✅ Uses Flask for HTTP server
- ✅ Imports from `core_engine` (one-way dependency)
- ✅ NO frontend dependencies
- ✅ Acts as adapter layer between frontend and core

**Responsibilities:**
- HTTP API endpoints (`/api/generate-stories`, etc.)
- Authentication & authorization
- File upload handling
- Format conversion (core output → frontend format)
- Database operations

**Can be developed independently:** ✅ YES (with core_engine as dependency)

### ✅ **Frontend** (`src/frontend/`)

**Status: ✅ PROPERLY SEPARATED**

**Dependencies:**
- ✅ NO Python dependencies
- ✅ NO direct access to core_engine
- ✅ Only uses REST API calls to backend
- ✅ Pure HTML/CSS/JavaScript

**Communication:**
- Uses `fetch()` API to call backend endpoints
- `/api/generate-stories` - Generate stories
- `/api/integrate-story` - Integrate story
- `/auth/*` - Authentication endpoints

**Can be developed independently:** ✅ YES (with backend API as dependency)

## Dependency Flow

```
Frontend (HTML/JS)
    ↓ (HTTP REST API)
Backend (Flask)
    ↓ (Python imports)
Core Engine (Pure Python)
```

**✅ Clean separation:** Each layer only depends on the layer below it.

## Issues Found

### ⚠️ **Issue 1: Code Duplication**

**Problem:**
- `src/core_engine/prompts.py` exists
- `autoAgile/utils/prompts.py` exists (similar functions)
- `src/backend/llm/prompts.py` exists (potential duplicate)

**Impact:**
- Maintenance burden - changes need to be made in multiple places
- Confusion about which version is "canonical"
- Risk of inconsistencies

**Recommendation:**
1. **Consolidate to `src/core_engine/`** as the single source of truth
2. Update all imports to use `core_engine` only
3. Mark `autoAgile/` as deprecated or remove it
4. Remove `src/backend/llm/` if it's duplicate

### ⚠️ **Issue 2: Mixed Imports**

**Current state in `src/backend/routes/api.py`:**
```python
from core_engine.prompts import (...)  # ✅ Good
from autoAgile.save_output import save_json_output  # ⚠️ Should use core_engine
```

**Recommendation:**
- Move `save_json_output` to `core_engine` or create a `core_engine/output.py`
- Update all imports to use `core_engine` only

## Recommendations for Better Separation

### 1. **Consolidate Core Engine**
```
src/core_engine/
├── __init__.py
├── prompts.py          # All LLM prompts
├── validation.py       # Validation logic
├── extraction.py       # Document extraction
└── output.py           # Output formatting/saving
```

### 2. **Clear Module Boundaries**

**Core Engine Interface:**
```python
# src/core_engine/__init__.py
from .prompts import (
    extract_text_from_docx,
    extract_epics,
    generate_test_cases,
    ...
)
from .validation import (
    validate_output,
    validate_requirements_completeness
)
from .output import save_json_output
```

**Backend Usage:**
```python
# src/backend/routes/api.py
from core_engine import (
    extract_text_from_docx,
    extract_epics,
    generate_test_cases,
    validate_output,
    save_json_output
)
```

### 3. **Create Clear API Contract**

**Backend API Contract:**
- Input: File upload (multipart/form-data)
- Output: JSON with stories array
- No direct file system access from frontend
- All business logic in core_engine

### 4. **Package Structure**

Consider making `core_engine` a proper Python package:
```
core_engine/
├── __init__.py
├── prompts/
│   ├── __init__.py
│   ├── extraction.py
│   ├── generation.py
│   └── refinement.py
├── validation/
│   ├── __init__.py
│   └── validators.py
└── output/
    ├── __init__.py
    └── formatters.py
```

## Testing Independence

### Core Engine Tests
- ✅ Can test without Flask
- ✅ Can test without database
- ✅ Pure unit tests possible

### Backend Tests
- ✅ Can mock core_engine
- ✅ Can test API endpoints independently
- ✅ Integration tests with core_engine

### Frontend Tests
- ✅ Can mock backend API
- ✅ Can test UI independently
- ✅ E2E tests with real backend

## Conclusion

### ✅ **Current State: GOOD SEPARATION**
- Core engine is independent ✅
- Backend properly uses core engine ✅
- Frontend properly uses REST API ✅

### ⚠️ **Improvements Needed**
1. Remove code duplication (consolidate to `core_engine`)
2. Update all imports to use `core_engine` only
3. Consider package structure improvements

### ✅ **Development Independence**
- **Core Engine:** Can be developed/tested independently ✅
- **Backend:** Can be developed independently (with core_engine dependency) ✅
- **Frontend:** Can be developed independently (with backend API) ✅

## Action Items

1. [ ] Audit `autoAgile/` vs `src/core_engine/` - identify differences
2. [ ] Consolidate duplicate code to `src/core_engine/`
3. [ ] Update all imports to use `core_engine` only
4. [ ] Remove or deprecate `autoAgile/` directory
5. [ ] Check `src/backend/llm/` - remove if duplicate
6. [ ] Create clear `core_engine` package interface
7. [ ] Update documentation with clear module boundaries
