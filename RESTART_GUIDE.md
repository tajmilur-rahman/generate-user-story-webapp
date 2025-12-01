# Quick Restart Guide 🔄

## The Problem

The validation improvements I added **won't take effect** until you restart the Flask server because Python loads the code once at startup.

## Current Issues in Generated Stories

Looking at your latest output, I can see these problems:

1. **❌ Poor Titles**
   - "Carry Out Some Initial Data"
   - "Include Some Mechanism Charge Its"
   - Should be: "Initial Data Processing", "Battery Charging System"

2. **❌ Template Test Cases**
   - "Test: [copy of requirement]"
   - "Expected: System performs [copy of requirement] successfully"
   - These are useless - not real test cases!

3. **❌ Circular Business Value**
   - "transmit data so that data can be processed" ❌
   - Should be: "transmit data so that weather forecasts can be generated" ✅

4. **❌ Invented Details in DoD**
   - Mentions CSV, JSON, XML when source might not specify
   - Needs to stick to source text only

## How to Restart Properly

### Windows (PowerShell):

1. **Stop the current server:**
   - Go to the terminal running `python app.py`
   - Press `Ctrl+C`

2. **Restart the server:**
   ```powershell
   python app.py
   ```

3. **Verify it restarted:**
   - Look for "[OK] Database tables created"
   - Look for "Running on http://127.0.0.1:5000"

## After Restart - Test Again

1. Upload your document again
2. Generate user stories
3. The validation should now:
   - ✅ Reject stories without proper "so that" clauses
   - ✅ Reject titles that are too short
   - ✅ Reject stories missing required fields
   - ✅ Log clear rejection reasons

## Expected Improvement

**Before (current):**
- 8 stories accepted (many with quality issues)
- Template test cases
- Poor titles

**After (with validation):**
- Only properly formatted stories accepted
- Rejection messages logged
- Easier to see what needs fixing

## If Still No Improvement After Restart

If you still see no improvement after restarting, I need to see:

1. The new log output showing rejection messages
2. How many stories are now being accepted
3. Examples of the "new" stories

Run this in PowerShell after generating stories:
```powershell
Get-Content app.log -Tail 50 | Select-String "REJECTED|Stories:"
```

This will show me:
- How many stories were rejected
- Why they were rejected
- How many stories passed validation

Then I can tune the validation or prompts further!
