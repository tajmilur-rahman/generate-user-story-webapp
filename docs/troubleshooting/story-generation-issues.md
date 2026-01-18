# User Story Generation Issues - Analysis

## Potential Issues Identified

### 1. **Overly Restrictive Prompt** ⚠️

The `extract_epics` prompt in `src/core_engine/prompts.py` has very strict rules:

**Current Issues:**
- **"EXPLICIT REQUIREMENTS ONLY"** - May be too restrictive, rejecting valid inferred requirements
- **"FORBIDDEN FEATURES"** - Long list of forbidden features might prevent useful stories
- **"SOURCE QUOTE MANDATORY"** - Every story must have exact quote, which might be too strict
- **"NO INVENTED METRICS"** - Good, but might be rejecting valid qualitative statements

**Location:** `src/core_engine/prompts.py` lines 354-367

### 2. **Strict Validation** ⚠️

The `validate_generated_stories` function in `story_service.py` rejects stories with:
- Fabricated quotes (stories without valid source quotes)
- This might be rejecting too many valid stories

**Location:** `src/backend/services/story_service.py` lines 340-421

### 3. **Low Temperature** ⚠️

Temperature is set to `0.3` which is quite low:
- Lower temperature = more deterministic, less creative
- Might need higher temperature (0.5-0.7) for more useful stories

**Location:** `src/backend/routes/api.py` line 79

### 4. **Requirements Extraction Issues** ⚠️

The `extract_functionarity` function uses multiple attempts (threshold=5) and consolidation:
- If requirements extraction fails or is poor quality, epics will be poor
- The `rat()` function might be adding too much refinement

**Location:** `src/core_engine/prompts.py` lines 252-314

## Recommendations

### Fix 1: Adjust Prompt to Be Less Restrictive

**Current prompt says:**
```
2. EXPLICIT REQUIREMENTS ONLY: Only extract requirements EXPLICITLY stated in source text. 
   Do NOT infer, assume, or add features based on best practices.
```

**Should be:**
```
2. REQUIREMENTS EXTRACTION: Extract requirements that are:
   - Explicitly stated in source text (preferred)
   - Reasonably inferred from context (when source text implies functionality)
   - Necessary for system completeness (when source describes a feature but not all details)
   
   DO NOT add features that are completely unrelated to the source text.
```

### Fix 2: Relax Source Quote Requirement

**Current:**
```
4. SOURCE QUOTE MANDATORY: Every requirement MUST include an exact quote from source text as evidence. 
   If no quote found, skip the requirement.
```

**Should be:**
```
4. SOURCE EVIDENCE: Every requirement should include:
   - An exact quote from source text (preferred), OR
   - A clear reference to the section/context in source text
   
   If no clear connection to source text exists, skip the requirement.
```

### Fix 3: Increase Temperature

Change temperature from `0.3` to `0.5` or `0.6` for more creative/useful stories.

### Fix 4: Review Validation Strictness

Check if `validate_generated_stories` is rejecting too many valid stories. Consider:
- Making quote validation less strict (allow paraphrases)
- Logging what's being rejected and why

## Diagnostic Steps

1. **Check Logs:**
   - Look at `data/logs/app.log` for validation errors
   - Check how many stories are being rejected

2. **Test with Sample Document:**
   - Upload a simple document
   - Check what requirements are extracted
   - Check what epics are generated
   - Check what gets rejected in validation

3. **Review LLM Output:**
   - Add logging to see raw LLM responses
   - Check if JSON parsing is failing
   - Check if stories are being filtered out

## Quick Fixes to Try

1. **Increase Temperature:**
   ```python
   # In src/backend/routes/api.py line 79
   temp = 0.6  # Instead of 0.3
   ```

2. **Relax Quote Validation:**
   ```python
   # In src/backend/services/story_service.py
   # Allow paraphrases, not just exact quotes
   ```

3. **Simplify Prompt:**
   - Remove overly restrictive rules
   - Focus on extracting useful stories
   - Keep validation for quality, not strictness
