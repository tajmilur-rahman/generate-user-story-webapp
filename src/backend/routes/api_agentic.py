"""
NEW Agentic API endpoint using ParallelStoryOrchestrator

This endpoint uses the parallel multi-agent architecture for MUCH faster generation.
Expected speedup: 8-10x faster than old autoAgile approach (25 min → 2-3 min)
"""

import os
import json
import tempfile
import time
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

def _build_deliverables(story):
    """
    Shape a story's deliverables for the frontend converter.

    The converter renders {category: {"definition_of_done": [items]}} as a
    heading per category with its items nested beneath, which is the legacy
    Definition of Done format:

        - Architecture Design:
          - Architecture diagram showing ...
          - Design doc for ...

    Falls back to a flat definition_of_done list if the model did not group
    its output into categories.

    Args:
        story: Story dictionary from the orchestrator

    Returns:
        Mapping of deliverable category to its nested items
    """
    deliverables = story.get("deliverables") or {}

    if isinstance(deliverables, dict) and deliverables:
        shaped = {}
        for category, items in deliverables.items():
            if isinstance(items, str):
                items = [items]
            items = [str(i).strip() for i in (items or []) if str(i).strip()]
            if items:
                shaped[str(category)] = {"definition_of_done": items}
        if shaped:
            return shaped

    # Older payloads: a flat list with no categories.
    flat = story.get("definition_of_done") or []
    if isinstance(flat, str):
        flat = [flat]
    flat = [str(i).strip() for i in flat if str(i).strip()]
    if flat:
        return {"definition_of_done": {"definition_of_done": flat}}

    return {}


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

    # Wall clock for the whole request: upload, parsing, generation and
    # conversion. Reported once at the end, after the conversion output.
    request_started = time.time()

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

        # Declared before the try so the failure handler can report the run id
        # and which phases completed, making the on-disk artifacts findable.
        orchestrator = None

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
            failures = result.get("failures", [])
            run_id = result.get("run_id")

            if failures:
                logger.warning(
                    f"Pipeline completed with {len(failures)} partial failure(s); "
                    f"output is incomplete"
                )
                for f in failures:
                    logger.warning(f"  [{f['phase']}] {f['detail']}: {f['error']}")

            logger.info(f"Generated: {len(requirements)} requirements, {len(epics)} epics, {len(stories)} stories, {len(test_cases)} test cases")

            # Coverage is the question the counts above do not answer: a run can
            # report plenty of stories while some requirements produced none.
            # Terminal only -- nothing here reaches the UI.
            covered = {str(s.get("requirement_id", "") or "").strip()
                       for s in stories if isinstance(s, dict)}
            uncovered = [r for r in requirements
                         if str(r.get("id", "") or "").strip() not in covered]
            if uncovered:
                logger.warning(
                    f"Coverage: {len(requirements) - len(uncovered)}/"
                    f"{len(requirements)} requirements produced a story"
                )
                for r in uncovered:
                    logger.warning(
                        f"    no story for {r.get('id', '?')}: "
                        f"{str(r.get('description', ''))[:70]}"
                    )
            else:
                logger.info(
                    f"Coverage: all {len(requirements)} requirements "
                    f"produced a story"
                )

            # Convert to format expected by old story_service
            # The orchestrator returns structured data; convert to the JSON string
            # format story_service expects.
            #
            # NOTE: the converter wants a FLAT list of stories under "User Stories".
            # Nesting them under "Epics" makes it treat each epic as a story and
            # discard every one of them as empty.
            # Definition of Done renders from "Deliverables" only.
            #
            # Acceptance Criteria is deliberately NOT passed: the converter
            # folds that key into the Definition of Done field, and DoD should
            # contain engineering deliverables, not restated criteria. The
            # criteria remain on the story data for dedup and review.
            epics_json = json.dumps({
                "User Stories": [
                    {
                        "User Story": story["user_story"],
                        # Model-written title; the converter derives one only
                        # when this is absent.
                        "Title": story.get("title", ""),
                        # Vocabulary not found in the source document. Carried
                        # for display; no story is removed because of it.
                        "Grounding": story.get("grounding", {}),
                        # Carried so the converter's deduplication can block on
                        # it: stories tracing to different requirements are not
                        # duplicates and must never be compared by similarity.
                        "Requirement ID": story.get("requirement_id", ""),
                        # Each category becomes its own heading with its items
                        # nested beneath, matching the legacy output format.
                        "Deliverables": _build_deliverables(story),
                        "Priority": story.get("priority", "Medium"),
                        "Estimation": story.get("story_points", "")
                    }
                    for story in stories
                ]
            }, indent=2)

            # Group test cases by requirement. The converter matches a group to a
            # story by text similarity against "requirement", so the requirement
            # description has to travel with the group, not just its ID.
            requirement_text_by_id = {
                req["id"]: req["description"] for req in requirements
            }

            tc_groups = {}
            for tc in test_cases:
                tc_groups.setdefault(tc.get("requirement_id", ""), []).append({
                    "id": tc.get("test_id", ""),
                    "description": tc.get("test_description", ""),
                    "steps": tc.get("test_steps", []),
                    "expected_result": tc.get("expected_result", "")
                })

            test_cases_json = json.dumps({
                "test_cases": [
                    {
                        "requirement_id": req_id,
                        "requirement": requirement_text_by_id.get(req_id, ""),
                        "test_cases": group
                    }
                    for req_id, group in tc_groups.items()
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

            total_seconds = time.time() - request_started
            elapsed = (f"{total_seconds:.1f}s" if total_seconds < 60
                       else f"{int(total_seconds // 60)}m {total_seconds % 60:04.1f}s")
            logger.info("=" * 60)
            logger.info(f"Completed in {elapsed}")
            logger.info("=" * 60)

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
                # A run that lost an epic must not look identical to a complete
                # one. Callers can surface this rather than silently shipping
                # fewer stories than the document warranted.
                'partial': bool(failures),
                'failures': failures,
                'run_id': run_id,
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

        # Surface the run id and completed phases. A failure late in the
        # pipeline no longer means the work is gone -- the artifacts for every
        # completed phase are on disk under this run id.
        run_id = getattr(orchestrator, 'run_id', None)
        completed = list(getattr(orchestrator, 'completed_phases', []))
        if run_id:
            logger.error(
                f"Run {run_id} failed after phases: {completed or 'none'}. "
                f"Partial results retained in {getattr(orchestrator, 'run_dir', '?')}"
            )

        return jsonify({
            'error': f'Error generating stories: {str(e)}',
            'details': traceback.format_exc().split(chr(10))[-5:],
            'run_id': run_id,
            'completed_phases': completed
        }), 500
