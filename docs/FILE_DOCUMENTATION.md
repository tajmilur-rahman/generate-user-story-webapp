# File Structure Documentation

This document provides a comprehensive overview of every file in the User Story Automation project and its purpose.

---

## 📁 Root Directory

### Configuration Files

#### `run.py`
- **Purpose**: Main application entry point
- **Function**: Launches the Flask web server
- **Usage**: Run `python run.py` to start the application

#### `requirements.txt`
- **Purpose**: Python dependencies list
- **Function**: Specifies all required Python packages
- **Usage**: Install with `pip install -r requirements.txt`

#### `package.json`
- **Purpose**: Node.js package configuration
- **Function**: Defines project metadata and npm scripts
- **Usage**: Used by npm for package management

#### `.env`
- **Purpose**: Environment variables configuration
- **Function**: Stores sensitive configuration (API keys, secrets)
- **Security**: ⚠️ Never commit to Git (already in .gitignore)

#### `.gitignore`
- **Purpose**: Git ignore rules
- **Function**: Specifies files/folders to exclude from version control
- **Includes**: venv/, __pycache__/, *.pyc, .env, logs, etc.

#### `.gitattributes`
- **Purpose**: Git attributes configuration
- **Function**: Defines how Git handles line endings and file types

---

## 📚 Documentation (`docs/`)

### `README.md`
- **Purpose**: Main documentation hub
- **Content**: Project overview, features, setup instructions
- **Audience**: All users and developers

### `GOOGLE_AUTH_SETUP.md`
- **Purpose**: Google OAuth configuration guide
- **Content**: Step-by-step Google authentication setup
- **Required for**: Google login feature

### `SMTP_EMAIL_SETUP.md`
- **Purpose**: Email service configuration guide
- **Content**: SMTP server setup for email notifications
- **Required for**: Email functionality

### `PROJECT_STRUCTURE.md`
- **Purpose**: Project architecture documentation
- **Content**: Directory structure and organization
- **Audience**: Developers

### `CROSS_PLATFORM_COMPATIBILITY.md`
- **Purpose**: Cross-platform setup notes
- **Content**: Platform-specific configuration (Windows, Linux, macOS)
- **Audience**: Developers on different OS

---

## 📄 Setup Guides (Root)

### `QUICK_SETUP.md`
- **Purpose**: Quick start guide
- **Content**: Minimal steps to get the app running
- **Audience**: New users wanting fast setup

### `UBUNTU_SETUP.md`
- **Purpose**: Ubuntu-specific setup guide
- **Content**: Detailed Ubuntu/Linux installation steps
- **Audience**: Linux users

### `TESTING_GUIDE.md`
- **Purpose**: Testing documentation
- **Content**: How to run tests, test structure, coverage
- **Audience**: Developers and QA

---

## 🔧 Configuration (`config/`)

### `SECRET_KEY.txt`
- **Purpose**: Flask secret key storage
- **Function**: Stores the secret key for session encryption
- **Security**: ⚠️ Auto-generated, never commit to Git

---

## 💾 Data Directories (`data/`)

### `data/logs/`
- **Purpose**: Application log storage
- **Files**: `app.log` - Runtime logs
- **Usage**: Debugging and monitoring

### `data/uploads/`
- **Purpose**: Temporary file upload storage
- **Files**: User-uploaded documents (.docx, .txt, .md)
- **Cleanup**: Files are deleted after processing

### `data/outputs/`
- **Purpose**: Generated output storage
- **Files**: JSON files with generated user stories
- **Format**: `{filename}.txt` or `{filename}.json`

---

## 🖥️ Backend (`src/backend/`)

### Main Application

#### `__init__.py`
- **Purpose**: Backend package initializer
- **Function**: Makes backend a Python package

#### `app.py`
- **Purpose**: Flask application factory
- **Function**: Creates and configures the Flask app
- **Key Features**:
  - CORS configuration
  - Route registration
  - Database initialization
  - Authentication setup
  - Session management

---

### Models (`src/backend/models/`)

#### `__init__.py`
- **Purpose**: Models package initializer
- **Function**: Exports database and user models

#### `database.py`
- **Purpose**: Database configuration
- **Function**: SQLAlchemy database instance
- **Database**: SQLite (users.db)

#### `user.py`
- **Purpose**: User model definition
- **Function**: Defines User table schema
- **Fields**: id, username, email, password_hash, google_id, created_at

---

### Routes (`src/backend/routes/`)

#### `__init__.py`
- **Purpose**: Routes package initializer
- **Function**: Registers all route blueprints

#### `api.py`
- **Purpose**: API endpoints
- **Function**: Handles user story generation and export
- **Endpoints**:
  - `POST /api/generate-stories` - Generate user stories from document
  - `POST /api/integrate-story` - Integrate single story
  - `POST /api/integrate-all` - Integrate all stories
  - `POST /api/export-json` - Export stories as JSON
  - `POST /api/export-docx` - Export stories as DOCX

#### `auth.py`
- **Purpose**: Authentication routes
- **Function**: Handles user login, registration, logout
- **Endpoints**:
  - `GET /auth/login` - Login page
  - `POST /auth/login` - Process login
  - `GET /auth/register` - Registration page
  - `POST /auth/register` - Process registration
  - `GET /auth/logout` - Logout
  - `GET /auth/google` - Google OAuth login
  - `GET /auth/google/callback` - Google OAuth callback
  - `GET /auth/status` - Check authentication status

#### `frontend.py`
- **Purpose**: Frontend page routes
- **Function**: Serves HTML pages
- **Endpoints**:
  - `GET /` - Home page
  - `GET /stories` - Stories page

---

### Services (`src/backend/services/`)

#### `__init__.py`
- **Purpose**: Services package initializer
- **Function**: Exports service modules

#### `story_service.py`
- **Purpose**: User story processing logic
- **Function**: Converts, validates, and sanitizes user stories
- **Key Functions**:
  - `convert_stories_to_frontend_format()` - Converts LLM output to frontend format
  - `validate_generated_stories()` - Validates story quality (currently disabled)
  - `sanitize_stories()` - Cleans and formats stories
  - `validate_story_coverage()` - Checks story count
  - `log_quality_metrics()` - Logs quality statistics

#### `email_service.py`
- **Purpose**: Email notification service
- **Function**: Sends email notifications
- **Features**: SMTP configuration, email templates
- **Status**: Optional (requires SMTP setup)

---

### Utilities (`src/backend/utils/`)

#### `__init__.py`
- **Purpose**: Utils package initializer

#### `helpers.py`
- **Purpose**: Helper functions
- **Function**: Common utility functions used across the app
- **Examples**: File validation, text processing, etc.

---

## 🤖 Core Engine (`src/core_engine/`)

### Main Files

#### `__init__.py`
- **Purpose**: Core engine package initializer

#### `prompts.py`
- **Purpose**: LLM prompt templates and logic
- **Function**: Defines all prompts for LLM interactions
- **Key Functions**:
  - `extract_functionarity()` - Extracts requirements from document
  - `extract_epics()` - Generates user stories/epics
  - `get_epics()` - Refines epics with definition of done (currently skipped)
  - `generate_test_cases()` - Generates test cases
  - `refine_doc()` - Cleans and refines input document
  - `extract_json_from_response()` - Extracts JSON from LLM responses
  - `rat()` - Refinement and thought process
  - `c_o_t()` - Chain of thought reasoning
  - `rank_answer()` - Ranks multiple answers

#### `llm_factory.py`
- **Purpose**: LLM provider factory
- **Function**: Creates LLM instances based on provider
- **Supported Providers**:
  - OpenAI (GPT-4, GPT-3.5)
  - Groq (Llama 3.3 70B)
  - Ollama (Local models like llama3.2)
- **Key Function**: `get_chat_model()` - Returns configured LLM instance

#### `output.py`
- **Purpose**: Output file generation
- **Function**: Saves generated stories to files
- **Key Function**: `save_json_output()` - Saves JSON output

#### `validation.py`
- **Purpose**: Output validation logic
- **Function**: Validates generated user stories
- **Key Functions**:
  - `validate_output()` - Validates story quality
  - `validate_requirements_completeness()` - Checks coverage
  - `print_validation_report()` - Prints validation results

#### `cli.py`
- **Purpose**: Command-line interface
- **Function**: Allows running the engine from command line
- **Usage**: For testing and standalone execution

---

### Tests (`src/core_engine/tests/`)

#### `__init__.py`
- **Purpose**: Tests package initializer

#### `test_prompts.py`
- **Purpose**: Unit tests for prompt functions
- **Function**: Tests prompt generation and LLM interactions

#### `evaluation.py`
- **Purpose**: Evaluation metrics
- **Function**: Evaluates quality of generated stories

#### `resources.py`, `insulim_resources.py`, `weather_resouces.py`, `test_doc_resources.py`
- **Purpose**: Test data resources
- **Function**: Sample documents and expected outputs for testing

---

## 🎨 Frontend (`src/frontend/`)

### Templates (`src/frontend/templates/`)

#### `index.html`
- **Purpose**: Main application page
- **Function**: Document upload and story generation interface
- **Features**:
  - File upload form
  - Model selection (OpenAI/Groq/Ollama)
  - Story display area
  - Export buttons

#### `login.html`
- **Purpose**: Login page
- **Function**: User authentication interface
- **Features**:
  - Email/password login
  - Google OAuth login
  - Registration link

#### `stories.html`
- **Purpose**: Stories display page
- **Function**: Shows generated user stories
- **Features**: Story list, filtering, export options

---

### Static Files (`src/frontend/static/`)

#### `css/styles.css`
- **Purpose**: Application styling
- **Function**: CSS styles for all pages
- **Features**:
  - Responsive design
  - Dark/light theme support
  - Component styling

#### `js/script.js`
- **Purpose**: Frontend JavaScript logic
- **Function**: Handles user interactions and API calls
- **Key Functions**:
  - `generateUserStories()` - Calls API to generate stories
  - `displayStories()` - Renders stories on page
  - `exportToJSON()` - Exports stories as JSON
  - `exportToDocx()` - Exports stories as DOCX
  - File upload handling
  - Error handling and notifications

---

## 🧪 Tests (`tests/`)

### `test_api.py`
- **Purpose**: API endpoint tests
- **Function**: Tests all API routes
- **Coverage**: /api/generate-stories, /api/export-*, etc.

### `test_bug_fixes.py`
- **Purpose**: Regression tests
- **Function**: Tests for previously fixed bugs
- **Purpose**: Ensures bugs don't reoccur

### `test_erie_generation.py`
- **Purpose**: Epic generation tests
- **Function**: Tests epic/story generation logic
- **Coverage**: End-to-end story generation

---

## 📊 Summary

### Total Files: ~50
- **Python Files**: 30
- **Documentation**: 9
- **Frontend**: 5 (HTML, CSS, JS)
- **Configuration**: 6

### Key Technologies:
- **Backend**: Flask, SQLAlchemy, Flask-Login
- **LLM**: LangChain, OpenAI, Groq, Ollama
- **Frontend**: HTML, CSS, JavaScript
- **Database**: SQLite
- **Authentication**: Flask-Login, Google OAuth

---

## 🔄 Data Flow

1. **User uploads document** → `index.html` → `script.js`
2. **API call** → `api.py` → `generate_stories()`
3. **Document processing** → `prompts.py` → LLM calls
4. **Story generation** → `extract_epics()`, `generate_test_cases()`
5. **Format conversion** → `story_service.py` → `convert_stories_to_frontend_format()`
6. **Validation** (disabled) → `validate_generated_stories()`
7. **Response** → JSON → `script.js` → Display on page
8. **Export** → `export_json()` or `export_docx()` → Download file

---

## 🔐 Security Notes

### Never Commit:
- `.env` - Contains API keys and secrets
- `config/SECRET_KEY.txt` - Flask secret key
- `instance/users.db` - User database
- `data/logs/*.log` - Log files
- `data/uploads/*` - Uploaded files
- `data/outputs/*` - Generated outputs

### Protected by .gitignore:
All sensitive files are already configured in `.gitignore`

---

## 📝 Notes

- **Validation is currently disabled** to allow all generated stories through
- **Epic refinement is skipped** to avoid JSON parsing errors with smaller LLMs
- **Ollama (llama3.2)** is the default LLM but produces lower quality output
- **For better results**: Use OpenAI GPT-4 or Groq Llama 3.3 70B

---

*Last Updated: 2026-01-29*
*Generated by: Antigravity AI Assistant*
