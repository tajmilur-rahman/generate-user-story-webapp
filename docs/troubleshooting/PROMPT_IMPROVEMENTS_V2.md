# Enhanced Prompts for Better Ollama Performance

## Overview

All prompts have been significantly improved to work better with Ollama and generate more useful, actionable user stories.

## Key Improvements

### 1. ✅ Document Cleaning (`clean_doc`)

**Before:** Basic grammar correction
**After:** Comprehensive document refinement with clear rules

**Improvements:**
- Clear process steps
- Explicit rules about what to preserve
- Better instructions for maintaining technical content

### 2. ✅ Requirements Extraction (`extract_list`)

**Before:** Simple extraction with basic rules
**After:** Structured methodology with step-by-step process

**Improvements:**
- Clear 3-step methodology
- Better requirement identification guidance
- Improved output format with confidence levels
- Quality checklist

### 3. ✅ User Story Generation (`extract_epics`)

**Before:** Restrictive rules, generic format
**After:** Comprehensive story creation with clear structure

**Major Improvements:**
- **4-step extraction process** (Analyze → Create → Define → Add Evidence)
- **Better user story format:** "As a [stakeholder], I need the system to [action] so that [value]"
- **Clear stakeholder identification** guidance
- **Concrete examples** of good user stories
- **Validation checklist** before output
- Less restrictive while maintaining quality

### 4. ✅ Test Case Generation (`generate_test_cases`)

**Before:** Long list of forbidden patterns
**After:** Clear process with concrete examples

**Major Improvements:**
- **4-step test case creation process**
- **Concrete examples** with real data structures
- **Clear distinction** between good and bad patterns
- **Better format guidance** with specific examples
- **Quality checklist** for validation

### 5. ✅ Requirements Refinement (`refine_requirements`)

**Before:** Generic consolidation instructions
**After:** Structured refinement process

**Improvements:**
- 4-step refinement process
- Clear DO/DON'T guidelines
- Better output format examples
- Validation steps

## Prompt Structure Improvements

### Better Organization
- **Step-by-step processes** instead of bullet lists
- **Clear sections** (GOAL, PROCESS, RULES, EXAMPLES)
- **Validation checklists** before output
- **Concrete examples** showing good vs bad

### Ollama-Specific Optimizations
- **Explicit instructions** (Ollama benefits from clear, direct commands)
- **Structured format** (easier for LLM to follow)
- **Examples embedded** in prompts (few-shot learning)
- **Validation steps** (helps LLM self-check)

### Quality Focus
- **Actionable output** (stories developers can implement)
- **Concrete data** (not generic templates)
- **Source evidence** (traceability maintained)
- **Useful content** (not just compliant)

## Expected Results

### Better Story Quality
- More useful, actionable user stories
- Clear stakeholder, action, and value
- Better deliverables with specific DoD
- Proper source evidence

### Better Test Cases
- Concrete input/output data
- Real data structures
- Specific scenarios
- No generic templates

### Better Requirements
- Clearer, more organized
- Better consolidation
- Maintained completeness
- Actionable format

## Configuration

Temperature is now configurable:
```bash
# In .env file
LLM_TEMPERATURE=0.5  # Default: balanced
LLM_TEMPERATURE=0.6  # More creative/useful
LLM_TEMPERATURE=0.4  # More deterministic
```

## Testing

After these improvements:
1. Upload a document
2. Check if stories are more useful and actionable
3. Verify test cases have concrete data
4. Review requirements organization

## Technical Details

### Prompt Structure Pattern
All prompts now follow this structure:
1. **Role/Goal** - Clear statement of what the LLM should do
2. **Process** - Step-by-step methodology
3. **Rules** - Critical guidelines (DO/DON'T)
4. **Format** - Exact output format with examples
5. **Validation** - Checklist before output

This structure works well with Ollama's instruction-following capabilities.
