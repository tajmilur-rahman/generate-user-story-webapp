# Project Structure

This document describes the organization of the User Story Automation project.

## Directory Structure

```
user-story-automation/
├── src/                          # Source code
│   ├── backend/                  # Flask backend application
│   │   ├── app.py                # Flask app initialization
│   │   ├── routes/                # API routes
│   │   │   ├── api.py            # Main API endpoints
│   │   │   ├── auth.py           # Authentication routes
│   │   │   └── frontend.py       # Frontend serving routes
│   │   ├── services/              # Business logic
│   │   │   ├── story_service.py  # Story processing service
│   │   │   └── email_service.py  # Email service
│   │   ├── models/                # Database models
│   │   │   ├── database.py       # Database setup
│   │   │   └── user.py           # User model
│   │   └── utils/                 # Backend utilities
│   │       └── helpers.py        # Helper functions
│   │
│   ├── autoAgile/                  # Core business logic (autoAgile engine)
│   │   ├── utils/                  # Utility modules
│   │   │   ├── prompts.py          # LLM prompts
│   │   │   ├── llm_factory.py      # LLM initialization (OpenAI, Ollama, Groq)
│   │   │   └── utils.py            # Helper utilities
│   │   ├── autoAgile.py            # Main CLI script
│   │   ├── save_output.py          # Output formatting/saving
│   │   ├── tests/                  # Test data and evaluation
│   │   │   ├── docs/               # Test documents (.docx)
│   │   │   ├── resources.py        # Test data
│   │   │   ├── test_prompts.py     # Prompt tests
│   │   │   └── evaluation.py       # Evaluation metrics
│   │   └── __init__.py             # Package exports
│   │
│   └── frontend/                   # Frontend assets
│       ├── templates/             # HTML templates
│       │   ├── index.html        # Main page
│       │   ├── login.html        # Login page
│       │   └── stories.html      # Stories display page
│       └── static/                # Static assets
│           ├── css/
│           │   └── styles.css    # Styles
│           └── js/
│               └── script.js      # Frontend JavaScript
│
├── tests/                         # Test files
│   ├── test_api.py               # API tests
│   ├── test_bug_fixes.py         # Bug fix tests
│   ├── test_erie_generation.py   # Erie-specific tests
│   ├── fixtures/                  # Test fixtures
│   ├── integration/               # Integration tests
│   └── unit/                      # Unit tests
│
├── config/                        # Configuration files
│   ├── nginx.conf                # Nginx configuration
│   └── SECRET_KEY.txt            # Secret key (should be in .env)
│
├── data/                          # Data files
│   ├── logs/                      # Application logs
│   │   ├── app.log               # Main application log
│   │   └── quality_metrics.jsonl # Quality metrics log
│   ├── outputs/                   # Generated outputs
│   └── uploads/                   # Uploaded files (temporary)
│
├── docs/                          # Documentation
│   ├── README.md                 # Main documentation
│   ├── PROJECT_STRUCTURE.md      # This file
│   ├── features/                  # Feature documentation
│   ├── setup/                     # Setup guides
│   └── troubleshooting/           # Troubleshooting guides
│
├── FINAL_STRUCTURE.md             # Final structure documentation
├── MIGRATION_GUIDE.md             # Migration guide (historical)
├── CONSOLIDATION_SUMMARY.md       # Consolidation summary (historical)
│
├── instance/                       # Application instance data
│   └── users.db                   # SQLite database
│
├── .env                           # Environment variables (create from config/env.template)
├── config/
│   ├── env.template              # Environment variables template
├── requirements.txt               # Python dependencies
├── package.json                   # Node.js dependencies (if any)
├── run.py                         # Application entry point
└── README.md                      # Project README
```

## Key Directories

### `src/` - Source Code
- **`backend/`**: Flask application, API routes, services, models
- **`autoAgile/`**: Core business logic (autoAgile engine, independent, can be developed separately)
- **`frontend/`**: HTML, CSS, JavaScript for web interface

### `tests/` - Tests
- Unit tests, integration tests, and test fixtures
- Organized by test type (unit, integration, etc.)

### `config/` - Configuration
- Configuration files, secrets (should use `.env` instead of `SECRET_KEY.txt`)

### `data/` - Data Files
- Logs, outputs, temporary uploads
- All data files organized under `data/`

### `docs/` - Documentation
- All documentation in one place
- Setup guides, architecture docs, troubleshooting

## File Organization Principles

1. **Separation of Concerns**
   - Core engine is independent
   - Backend depends on core engine
   - Frontend depends on backend API

2. **Clear Structure**
   - Related files grouped together
   - Configuration in `config/`
   - Data in `data/`
   - Documentation in `docs/`

3. **No Root Clutter**
   - Minimal files at root level
   - Only essential files: `run.py`, `requirements.txt`, `README.md`, `.env`

4. **Logical Grouping**
   - Scripts organized by purpose
   - Tests organized by type
   - Documentation organized by topic

## Important Files

### Entry Points
- `run.py` - Main application launcher

### Configuration
- `.env` - Environment variables (create from `config/env.template`)
- `requirements.txt` - Python dependencies

### Documentation
- `README.md` - Project overview
- `docs/README.md` - Detailed documentation
- `UBUNTU_SETUP.md` - Complete tested Ubuntu installation guide
- `QUICK_SETUP.md` - Quick setup with all commands

## Data Files Location

- **Logs**: `data/logs/`
- **Outputs**: `data/outputs/`
- **Uploads**: `data/uploads/` (temporary)
- **Database**: `instance/users.db`

## Notes

- The `autoAgile/` directory contains the core engine from the autoAgile project
- All core functionality has been consolidated into `src/autoAgile/`
- Configuration should use `.env` file, not `config/SECRET_KEY.txt`
- Test files reference data files using relative paths from project root
- Output files are saved to `data/outputs/`