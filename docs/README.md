# User Story Automation

Full-stack application for generating and managing user stories from project documents. Features a Flask server that serves both the frontend web interface and backend API - no additional web server needed!

## Quick Start

### Prerequisites

- Python 3.8+ installed
- (Optional) Ollama installed for local LLM, or OpenAI API key

### Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables (optional):**
   ```bash
   # Create .env file with (or use defaults):
   # USE_OLLAMA=true
   # OLLAMA_BASE_URL=http://localhost:11434
   # OLLAMA_MODEL=llama3.2
   # Or for OpenAI:
   # USE_OLLAMA=false
   # auth_key=your_openai_api_key_here
   ```

3. **Start the application:**
   ```bash
   # From project root
   python app.py
   ```

4. **Access the application:**
   - **Frontend & API**: http://localhost:5000
   - **Health check**: http://localhost:5000/api/health

That's it! Flask serves both the frontend and API on port 5000.

### Stop Server

Press `Ctrl+C` in the terminal running `app.py`

## Project Structure

```
.
├── app.py              # Flask backend API server
├── requirements.txt    # Python dependencies
├── .env.example       # Environment variables template
├── pages/              # HTML pages
│   ├── index.html      # Main page - file upload and story generation
│   └── stories.html    # Stories list and details
├── assets/             # Static assets
│   ├── css/
│   │   └── styles.css
│   └── js/
│       └── script.js   # Frontend JavaScript (connected to backend)
├── autoAgile/          # Backend processing module
│   ├── utils/
│   │   └── prompts.py  # LLM prompts and processing functions
│   └── save_output.py
├── config/             # Configuration
│   └── nginx.conf      # Nginx server configuration (with API proxy)
├── scripts/            # Utility scripts
│   ├── start.sh        # Start nginx server
│   ├── stop.sh         # Stop nginx server
│   └── force-stop.sh   # Force stop nginx
├── docs/               # Documentation
│   ├── SETUP.md        # Setup instructions
│   └── INTEGRATION.md  # Backend integration guide
└── package.json        # npm scripts
```

## Features

- **Document Upload**: Upload .docx, .doc, .txt, or .md files with project requirements
- **AI-Powered Generation**: Uses LLM (Ollama or OpenAI) to generate user stories
- **Story Management**: View generated stories with:
  - Title and Description
  - Definition of Done
  - Test Cases
- **Integration**: Integrate individual stories or all stories at once
- **Dual LLM Support**: Works with Ollama (free, local) or OpenAI (cloud-based)

## Running the Application

```bash
python app.py  # Start the server (serves frontend + API on port 5000)
```

The Flask server serves:
- Frontend pages (HTML)
- Static assets (CSS, JS)
- API endpoints

No nginx or separate frontend server needed!

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Use Ollama (free, local) - default: true
USE_OLLAMA=true

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# OR use OpenAI (requires API key)
# USE_OLLAMA=false
# auth_key=your_openai_api_key_here

# Flask Server Port
PORT=5000
```

### Setting up Ollama (Recommended for Free Usage)

1. Install Ollama: https://ollama.ai
2. Pull a model:
   ```bash
   ollama pull llama3.2
   # or
   ollama pull mistral
   ```
3. Make sure Ollama is running: `ollama serve`

### Setting up OpenAI

1. Get API key from: https://platform.openai.com/api-keys
2. Set `USE_OLLAMA=false` in `.env`
3. Set `auth_key=your_api_key_here` in `.env`

## API Endpoints

The Flask backend provides the following endpoints:

- `GET /api/health` - Health check and configuration status
- `POST /api/generate-stories` - Generate stories from uploaded document
  - **Request**: FormData with `file` field (.docx, .doc, .txt, .md)
  - **Response**: `{ success: true, stories: [...], count: N }`
- `POST /api/integrate-story` - Integrate a single story
  - **Request**: `{ storyId: number }`
  - **Response**: `{ success: true, message: "...", storyId: number }`
- `POST /api/integrate-all` - Integrate all stories
  - **Request**: `{ storyIds: [number, ...] }`
  - **Response**: `{ success: true, message: "...", storyIds: [...] }`

**Story format:**
```json
{
  "success": true,
  "stories": [{
    "id": 1,
    "title": "Story title",
    "description": "Story description",
    "definitionOfDone": "Definition of done",
    "testCases": "Test cases"
  }],
  "count": 1
}
```

## Troubleshooting

### Backend not responding
- Make sure Flask server is running: `python app.py`
- Check if port 5000 is available
- Verify environment variables in `.env` file

### Frontend can't connect to backend
- Ensure nginx is running: `npm run status`
- Check nginx config: `npm test`
- Verify API proxy in `config/nginx.conf` points to `http://localhost:5000`

### Story generation fails
- If using Ollama: Ensure Ollama is running (`ollama serve`)
- If using OpenAI: Verify API key is correct and has credits
- Check file size (max 16MB)
- Supported formats: .docx, .doc, .txt, .md

## Documentation

- [docs/SETUP.md](docs/SETUP.md) - Setup and installation instructions
- [docs/INTEGRATION.md](docs/INTEGRATION.md) - Backend integration guide
