"""
NEW Agentic API endpoint using ParallelStoryOrchestrator

This endpoint uses the parallel multi-agent architecture for MUCH faster generation.
Expected speedup: 8-10x faster than old autoAgile approach (25 min → 2-3 min)
"""

import os
import json
import tempfile
import logging
import traceback
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from backend.utils.helpers import allowed_file
from backend.services.story_service import convert_stories_to_frontend_format
from autoAgile.utils.prompts import extract_text_from_docx
from agents import ParallelStoryOrchestrator
from autoAgile.save_output import save_json_output

api_agentic_bp = Blueprint('api_agentic', __name__)
logger = logging.getLogger(__name__)

# Configuration
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'qwen3-coder:30b')
MAX_WORKERS = int(os.environ.get('MAX_PARALLEL_WORKERS', '5'))

@api_agentic_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for agentic architecture"""
    return jsonify({
        'status': 'ok',
        'architecture': 'parallel-agentic',
        'ollama_url': OLLAMA_BASE_URL,
        'model': OLLAMA_MODEL,
        'max_workers': MAX_WORKERS,
        'version': '2.0-parallel'
    })

@api_agentic_bp.route('/generate-stories-agentic', methods=['POST'])
@login_required
def generate_stories_agentic():
    """
    Generate user stories using parallel multi-agent architecture

    This endpoint is 8-10x faster than the old autoAgile approach.
    Expected time: 2-3 minutes (vs 25 minutes with old approach)
    """
    logger.info("=" * 60)
    logger.info("API CALL RECEIVED: /api/agentic/generate-stories-agentic")
    logger.info("Using PARALLEL MULTI-AGENT ARCHITECTURE")
    logger.info(f"Workers: {MAX_WORKERS}, Model: {OLLAMA_MODEL}")
    logger.info("=" * 60)

    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed. Please upload .docx, .doc, .txt, or .md files'}), 400

        # Save uploaded file temporarily
        filename = secure_filename(file.filename)

        # Handle macOS resource fork files (._filename) - skip them
        if filename.startswith('._'):
            return jsonify({'error': 'Invalid file: macOS resource fork file detected. Please upload the actual document file.'}), 400

        upload_folder = current_app.config.get('UPLOAD_FOLDER', tempfile.gettempdir())
        filepath = os.path.join(upload_folder, filename)

        # Save the file
        file.save(filepath)

        # Verify file was saved and exists
        if not os.path.exists(filepath):
            return jsonify({'error': f'Failed to save uploaded file to {filepath}'}), 500

        # Verify file is not empty
        if os.path.getsize(filepath) == 0:
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': 'Uploaded file is empty'}), 400

        logger.info(f"File saved: {filepath} ({os.path.getsize(filepath)} bytes)")

        try:
            # Extract text from document
            if filename.endswith('.docx') or filename.endswith('.doc'):
                document_text = extract_text_from_docx(filepath)
            else:
                with open(filepath, 'r', encoding='utf-8') as f:
                    document_text = f.read()

            logger.info(f"Document extracted: {len(document_text)} characters")

            # Initialize parallel orchestrator
            logger.info(f"Initializing ParallelStoryOrchestrator with {MAX_WORKERS} workers...")
            orchestrator = ParallelStoryOrchestrator(max_workers=MAX_WORKERS)

            # Generate stories using parallel agents
            logger.info("Starting parallel story generation pipeline...")
            result = orchestrator.generate_stories(document_text)

            # Extract results
            requirements = result["requirements"]
            epics = result["epics"]
            stories = result["stories"]
            test_cases = result["test_cases"]
            execution_time = result.get("execution_time", 0)

            logger.info(f"Pipeline complete in {execution_time:.1f}s ({execution_time/60:.1f} min)")
            logger.info(f"Generated: {len(requirements)} requirements, {len(epics)} epics, {len(stories)} stories, {len(test_cases)} test cases")

            # Convert to format expected by old story_service
            # The orchestrator returns structured data, we need to convert to the old JSON string format
            epics_json = json.dumps({
                "Epics": [
                    {
                        "Epic Name": epic["epic_name"],
                        "Description": epic["description"],
                        "Requirements": epic["requirement_ids"],
                        "Stories": [
                            {
                                "User Story": story["user_story"],
                                "Acceptance Criteria": story.get("acceptance_criteria", []),
                                "Definition of Done": story.get("definition_of_done", ""),
                                "Priority": story.get("priority", "Medium"),
                                "Estimation": story.get("estimation", "")
                            }
                            for story in stories
                            if story.get("epic_id") == epic["epic_id"]
                        ]
                    }
                    for epic in epics
                ]
            }, indent=2)

            test_cases_json = json.dumps({
                "test_cases": [
                    {
                        "requirement_id": tc["requirement_id"],
                        "test_cases": [
                            {
                                "id": tc["test_id"],
                                "description": tc["test_description"],
                                "steps": tc.get("test_steps", []),
                                "expected": tc.get("expected_result", "")
                            }
                        ]
                    }
                    for tc in test_cases
                ]
            }, indent=2)

            requirements_text = "\n".join([
                f"{req['id']}: {req['description']}"
                for req in requirements
            ])

            # Convert to frontend format using existing service
            logger.info("Converting to frontend format...")
            frontend_stories = convert_stories_to_frontend_format(
                epics_json,
                test_cases_json,
                requirements_text
            )

            logger.info(f"Converted to {len(frontend_stories)} frontend stories")

            if not frontend_stories or len(frontend_stories) == 0:
                logger.error("WARNING: No stories generated after conversion!")
                return jsonify({
                    'success': False,
                    'error': 'No user stories were generated. Please check the server logs for details.',
                    'stories': [],
                    'count': 0
                }), 500

            # Save output to JSON file
            output_file_path = None
            try:
                output_file_path = save_json_output(
                    requirements_text,
                    epics_json,
                    test_cases_json,
                    filepath
                )
                logger.info(f"Output saved to: {output_file_path}")
            except Exception as save_error:
                logger.error(f"Could not save JSON output: {save_error}")

            return jsonify({
                'success': True,
                'stories': frontend_stories,
                'count': len(frontend_stories),
                'output_file': output_file_path,
                'execution_time': execution_time,
                'performance': {
                    'total_seconds': round(execution_time, 1),
                    'total_minutes': round(execution_time / 60, 2),
                    'requirements_count': len(requirements),
                    'epics_count': len(epics),
                    'stories_count': len(stories),
                    'test_cases_count': len(test_cases),
                    'workers_used': MAX_WORKERS
                }
            })

        finally:
            # Clean up temporary file
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Cleaned up temporary file: {filepath}")

    except Exception as e:
        logger.error(f"Error generating stories: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': f'Error generating stories: {str(e)}',
            'details': traceback.format_exc().split('\n')[-5:]
        }), 500
