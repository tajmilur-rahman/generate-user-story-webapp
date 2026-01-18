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
│   │   ├── utils/                 # Backend utilities
│   │   │   └── helpers.py        # Helper functions
│   │   └── llm/                   # LLM-related code (legacy)
│   │
│   ├── core_engine/               # Core business logic (independent)
│   │   ├── prompts.py            # LLM prompts and story generation
│   │   ├── validation.py         # Output validation
│   │   ├── output.py              # Output formatting/saving
│   │   └── __init__.py           # Package exports
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
├── scripts/                        # Utility scripts
│   ├── setup/                     # Setup scripts
│   │   ├── setup.sh              # Complete setup (Ubuntu/Linux - installs everything)
│   │   ├── setup.bat             # Basic setup (Windows - Python dependencies only)
│   │   └── setup.ps1              # Basic setup (Windows PowerShell - Python dependencies only)
│   ├── start.sh                  # Start server (Linux/Mac)
│   ├── stop.sh                   # Stop server (Linux/Mac)
│   └── force-stop.sh             # Force stop server
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
│   ├── SETUP.md                  # Setup guide
│   ├── REQUIREMENTS.md            # Requirements checklist
│   ├── ARCHITECTURE_SEPARATION.md # Architecture docs
│   ├── CONSOLIDATION_*.md         # Consolidation docs
│   ├── CLEANUP_*.md              # Cleanup docs
│   ├── features/                  # Feature documentation
│   ├── setup/                     # Setup guides
│   └── troubleshooting/           # Troubleshooting guides
│
├── autoAgile/                     # Legacy/backward compatibility
│   ├── json_output/               # JSON output storage
│   ├── tests/                     # Test fixtures/resources
│   └── utils/                     # Legacy utilities
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
- **`core_engine/`**: Core business logic (independent, can be developed separately)
- **`frontend/`**: HTML, CSS, JavaScript for web interface

### `tests/` - Tests
- Unit tests, integration tests, and test fixtures
- Organized by test type (unit, integration, etc.)

### `scripts/` - Utility Scripts
- Setup scripts, test runners, log readers, server management
- Setup scripts in `scripts/setup/` subdirectory

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
- `docs/SETUP.md` - Setup instructions

## Data Files Location

- **Logs**: `data/logs/`
- **Outputs**: `data/outputs/`
- **Uploads**: `data/uploads/` (temporary)
- **Database**: `instance/users.db`

## Notes

- The `autoAgile/` directory is kept for backward compatibility and test fixtures
- All core functionality has been consolidated into `src/core_engine/`
- Configuration should use `.env` file, not `config/SECRET_KEY.txt`
- Test files reference data files using relative paths from project root
