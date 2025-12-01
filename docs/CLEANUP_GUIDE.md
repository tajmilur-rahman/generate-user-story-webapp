# Old Code Cleanup Guide

## Current Situation

You now have **BOTH** old and new code structures:

### ✅ New Structure (KEEP - This is what's running)
```
src/backend/          ← Running code
src/frontend/         ← Running code
data/logs/           ← Log files
docs/                ← Documentation
```

### ❌ Old Structure (DELETE SAFE - Not being used)
```
app.py               ← Old launcher (replaced by run.py)
database.py          ← Old (now in src/backend/models/)
models.py            ← Old (now in src/backend/models/)
routes/              ← Old folder (now in src/backend/routes/)
services/            ← Old folder (now in src/backend/services/)
utils/               ← Old folder (now in src/backend/utils/)
assets/              ← Old folder (now in src/frontend/static/)
pages/               ← Old folder (now in src/frontend/templates/)
```

---

## What You Can Safely Delete

### Files to Delete:
```
app.py                    (old launcher)
database.py               (old database)
models.py                 (old models)
```

### Folders to Delete:
```
routes/                   (old routes)
services/                 (old services - but wait!)
utils/                    (old utils)
assets/                   (old frontend)
pages/                    (old templates)
__pycache__/             (Python cache)
.pytest_cache/           (test cache)
```

### ⚠️ WAIT on services/ folder!

Before deleting `services/story_service.py`, let me check if the NEW one is being used now.

---

## What to KEEP

### Essential Files:
```
run.py                   ← NEW launcher (keep!)
.env                     ← Environment variables (keep!)
.gitignore              ← Git config (keep!)
requirements.txt        ← Dependencies (keep!)
README.md               ← Documentation (keep!)
SECRET_KEY.txt          ← Secret key (keep!)
```

### Essential Folders:
```
src/                    ← NEW code structure (keep!)
instance/               ← Database files (keep!)
autoAgile/             ← Legacy LLM code (keep for now!)
tests/                 ← Test files (keep!)
scripts/               ← Utility scripts (keep!)
config/                ← Config files (keep!)
```

---

## Issue: Story Validation Too Strict

Before cleaning up, we need to fix the validation - it's rejecting ALL stories!

The problem: Validation requires "so that" clause, but LLM doesn't always include it.

### Quick Fix:

I can make the validation less strict so some stories pass through.

---

## Recommended Action

### Option 1: Fix Validation First, Then Clean (RECOMMENDED)
1. Let me make validation less strict
2. Test that stories generate
3. Then delete old files

### Option 2: Delete Old Code Now
1. Delete old files immediately
2. Fix validation after
3. Risk: If something breaks, old code is gone

**Which do you prefer?**

---

## Quick Delete Commands (When Ready)

```powershell
# When you're ready to delete old code:

# Delete old files
Remove-Item app.py, database.py, models.py

# Delete old folders (CAREFUL - make backup first!)
Remove-Item -Recurse -Force routes, services, utils, assets, pages, __pycache__, .pytest_cache

# Keep autoAgile for now (still needed for prompts)
```

---

## My Recommendation

**Fix validation → Test → Then delete old code**

This way:
1. ✅ Validation works
2. ✅ Stories generate properly
3. ✅ Safe to delete old code

Reply with:
- **"fix first"** → I'll make validation less strict
- **"delete now"** → I'll give you the cleanup commands
