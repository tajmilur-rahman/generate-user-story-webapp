# LLM Prompt Issues Analysis

## Critical Issues Found

### 1. **Inconsistent Output Format Between Prompt Files**
   - **Location**: `src/core_engine/prompts.py` vs `src/backend/llm/prompts.py`
   - **Issue**: 
     - `core_engine/prompts.py` (line 418): Returns `{"User Stories": [...]}`
     - `backend/llm/prompts.py` (line 483): Returns `{"Epics": [...]}`
   - **Impact**: LLM might get confused if using wrong file, or return wrong format
   - **Status**: ✅ FIXED - Using `core_engine/prompts.py` which has correct format

### 2. **Extremely Long Prompts (500+ lines)**
   - **Location**: `extract_epics()` function in `src/core_engine/prompts.py`
   - **Issue**: Prompt is over 500 lines with excessive repetition
   - **Impact**:
     - May hit token limits
     - LLM might miss critical instructions buried in verbose text
     - Higher API costs
     - Inconsistent outputs
   - **Recommendation**: Simplify and restructure prompt to be more concise

### 3. **Prompt Structure Issues**
   - **Too many emojis and formatting**: May confuse some LLM models
   - **Repetitive instructions**: Same rules stated multiple times
   - **Conflicting terminology**: Uses both "Epics" and "User Stories" in same prompt
   - **Example format mismatch**: Shows `"id"` field but may not be needed

### 4. **Missing Critical Instructions Clarity**
   - The prompt has good rules but they're buried in verbose text
   - Key instructions should be at the top, not scattered throughout

## Recommendations

1. **Standardize Output Format**: Ensure all prompts use `{"User Stories": [...]}` consistently
2. **Simplify Prompts**: Reduce from 500+ lines to ~200-300 lines with clear structure
3. **Restructure for Clarity**:
   - Put critical rules at the top
   - Use clear sections with headers
   - Remove excessive emojis
   - Consolidate repetitive instructions
4. **Add Validation**: Ensure prompt output matches expected format before processing

## Files to Fix

1. ✅ `src/core_engine/prompts.py` - Main file (being used)
2. ⚠️ `src/backend/llm/prompts.py` - Duplicate (should match or be removed)
3. ⚠️ `autoAgile/utils/prompts.py` - Another duplicate

## Next Steps

1. Fix output format consistency
2. Optimize prompt length and structure
3. Test with actual LLM calls
4. Remove or sync duplicate prompt files

