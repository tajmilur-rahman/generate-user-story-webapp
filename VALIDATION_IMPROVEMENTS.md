# User Story Validation Improvements ✅

## Changes Made

I've **tightened the validation** for user story generation to ensure only properly formatted stories are accepted.

## New Validation Rules

### ✅ **Format Validation (STRICT - Stories Rejected if Failed)**

Every user story must now pass these checks:

1. **Required Fields**
   - Must have: `User Story`, `Title`, `Deliverables`
   - All fields must be non-empty

2. **User Story Format**
   - Minimum 20 characters
   - Must contain action keywords: `must`, `shall`, `can`, `should`, or `will`
   - **Must include "so that" clause** for business value
   - Example: "The system must collect data so that weather patterns can be analyzed"

3. **Title Validation**
   - Minimum 3 characters
   - Must be descriptive

4. **Deliverables Validation**
   - Must be a dictionary (not empty)
   - Each deliverable must have a `definition_of_done` field
   - Definition of done must be at least 10 characters

5. **Rejection Criteria**
   - ❌ Missing fields → **REJECTED**
   - ❌ No "so that" clause → **REJECTED**
   - ❌ Too short → **REJECTED**
   - ❌ No action keywords → **REJECTED**
   - ❌ Invalid deliverables → **REJECTED**

### ⚠️ **Source Quote Validation (WARNING - Not Rejected)**

- Missing or invalid source quotes are logged as warnings
- Stories are **still included** even with quote issues
- This prevents over-strict filtering

## What Gets Rejected Now

**Before:** Stories were rejected only for fabricated quotes  
**After:** Stories are rejected for:
- Invalid format (no "must/shall/can/should/will")
- Missing "so that" clause
- Missing required fields
- Too short (< 20 chars)
- Invalid deliverables structure

## How It Works

```python
# Validation happens in this order:
1. Format validation (REJECTS if failed)
2. Source quote validation (WARNING only)
3. Invented metrics check (WARNING, cleaned)
4. Template detection (WARNING, cleaned)
5. Metadata leak check (WARNING, cleaned)
```

## Example Valid User Story

```json
{
  "id": 1,
  "Title": "Collect Weather Data",
  "User Story": "The system must collect temperature data every hour so that accurate weather forecasts can be provided",
  "source_quote": "...",
  "Deliverables": {
    "Data_Collection": {
      "definition_of_done": "System successfully collects temperature readings from all sensors"
    }
  }
}
```

## Example Invalid User Story (REJECTED)

```json
{
  "id": 1,
  "Title": "Data",
  "User Story": "Collect data",  // ❌ No "so that", too short, no keywords
  "Deliverables": {}  // ❌ Empty deliverables
}
```

## Next Steps

**Restart your server** to apply the new validation:

```bash
# Stop the server (Ctrl+C)
python app.py
```

Then try generating user stories again. The system will now:
- ✅ Only accept properly formatted stories
- ✅ Reject incomplete/malformed stories
- ✅ Log clear error messages about why stories were rejected

This should significantly improve the quality of generated user stories!
