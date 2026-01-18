# Prompt Improvements for Better User Story Generation

## Changes Made

### 1. ✅ Less Restrictive Requirements Extraction

**Before:**
```
2. EXPLICIT REQUIREMENTS ONLY: Only extract requirements EXPLICITLY stated in source text. 
   Do NOT infer, assume, or add features based on best practices.
```

**After:**
```
2. REQUIREMENTS EXTRACTION: Extract requirements that are:
   - Explicitly stated in source text (preferred)
   - Reasonably inferred from context (when source text implies functionality)
   - Necessary for system completeness (when source describes a feature but not all details)
   
   DO NOT add features that are completely unrelated to the source text.
```

**Impact:** Allows reasonable inference while still preventing hallucination.

### 2. ✅ Relaxed Source Quote Requirement

**Before:**
```
4. SOURCE QUOTE MANDATORY: Every requirement MUST include an exact quote from source text as evidence. 
   If no quote found, skip the requirement.
```

**After:**
```
4. SOURCE EVIDENCE: Every requirement should include:
   - An exact quote from source text (preferred), OR
   - A clear reference to the section/context in source text that supports the requirement
   
   If no clear connection to source text exists, skip the requirement.
```

**Impact:** Allows clear references when exact quotes aren't possible, reducing false rejections.

### 3. ✅ Increased Default Temperature

**Before:**
```python
temp = 0.3  # Very deterministic, less creative
```

**After:**
```python
temp = float(os.environ.get('LLM_TEMPERATURE', '0.5'))  # More creative, better for useful stories
```

**Impact:** Higher temperature (0.5) allows more creative and useful story generation while maintaining quality.

### 4. ✅ Added Goal Statement

**Before:**
```
You are a requirements extraction system. Extract user stories from the provided source text.
```

**After:**
```
You are a requirements extraction system. Extract useful, actionable user stories from the provided source text.

GOAL: Generate practical user stories that developers can actually implement. 
Focus on extracting meaningful functionality that adds value.
```

**Impact:** Explicitly guides the LLM to generate useful, actionable stories.

### 5. ✅ Updated Validation Rules

**Before:**
```
- All stories have source quotes
```

**After:**
```
- All stories have source evidence (quote or clear reference)
- Stories are useful and actionable (not too generic)
```

**Impact:** More flexible validation while ensuring quality.

## Configuration

### Temperature Setting

You can now control temperature via environment variable:

```bash
# In .env file
LLM_TEMPERATURE=0.5  # Default: balanced creativity
LLM_TEMPERATURE=0.6  # More creative/useful stories
LLM_TEMPERATURE=0.3  # More deterministic (if needed)
```

### Recommended Settings

- **For useful, actionable stories:** `LLM_TEMPERATURE=0.5` to `0.6`
- **For strict compliance:** `LLM_TEMPERATURE=0.3` to `0.4`

## Expected Improvements

1. **More Useful Stories** - Less restrictive rules allow reasonable inference
2. **Better Coverage** - Stories won't be rejected for minor quote issues
3. **More Creative** - Higher temperature generates more practical stories
4. **Actionable Content** - Explicit goal statement guides toward useful output

## Testing

After these changes:
1. Upload a document
2. Check if more stories are generated
3. Verify stories are useful and actionable
4. Check logs for validation warnings (should be fewer rejections)

## Rollback

If you need to revert:
1. Set `LLM_TEMPERATURE=0.3` in `.env`
2. The prompt changes are in `src/core_engine/prompts.py` - can be reverted if needed
