import os
import json
import tempfile
import logging
import traceback
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq


from backend.utils.helpers import allowed_file
from backend.services.story_service import convert_stories_to_frontend_format
from core_engine.prompts import (
    extract_text_from_docx, refine_doc, extract_functionarity,
    extract_epics, get_epics, generate_test_cases, refine_requirements, rat
)
from core_engine.output import save_json_output
from core_engine.validation import validate_output, validate_requirements_completeness, print_validation_report

api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

# LLM Configuration
LLM_PROVIDER = os.environ.get('LLM_PROVIDER', 'ollama').lower()
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '').strip()
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '') or os.environ.get('auth_key', '')
OPENAI_API_KEY = OPENAI_API_KEY.strip() if OPENAI_API_KEY else ''
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3.2:latest')

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok', 
        'provider': LLM_PROVIDER,
        'api_key_configured': bool(OPENAI_API_KEY if LLM_PROVIDER == 'openai' else GROQ_API_KEY if LLM_PROVIDER == 'groq' else True),
        'ollama_url': OLLAMA_BASE_URL if LLM_PROVIDER == 'ollama' else None,
        'model': OLLAMA_MODEL if LLM_PROVIDER == 'ollama' else 'llama-3.3-70b-versatile' if LLM_PROVIDER == 'groq' else 'gpt-4o'
    })

@api_bp.route('/generate-stories', methods=['POST'])
@login_required
def generate_stories():
    """Generate user stories from uploaded document (requires authentication)"""
    logger.info("API CALL RECEIVED: /api/generate-stories")
    
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed. Please upload .docx, .doc, .txt, or .md files'}), 400

        # Validate API key based on provider
        if LLM_PROVIDER == 'openai' and not OPENAI_API_KEY:
            return jsonify({'error': 'OpenAI API key not configured. Set OPENAI_API_KEY in .env'}), 500
        elif LLM_PROVIDER == 'groq' and not GROQ_API_KEY:
            return jsonify({'error': 'Groq API key not configured. Set GROQ_API_KEY in .env'}), 500
        
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        
        # Handle macOS resource fork files (._filename) - skip them
        if filename.startswith('._'):
            return jsonify({'error': 'Invalid file: macOS resource fork file detected. Please upload the actual document file, not the resource fork.'}), 400
        
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
        
        logger.info(f"File saved successfully: {filepath} (size: {os.path.getsize(filepath)} bytes)")
        
        try:
            # Initialize LLM model based on configured provider
            # Higher temperature for more creative/useful stories (0.5-0.7 range)
            # Lower temperature for more deterministic output (0.3-0.4 range)
            temp = float(os.environ.get('LLM_TEMPERATURE', '0.5'))
            chat = None
            
            if LLM_PROVIDER == 'ollama':
                model_name = request.form.get('model', OLLAMA_MODEL)
                logger.info(f"[Ollama] Initializing with model: {model_name}")
                chat = ChatOllama(
                    model=model_name,
                    temperature=temp,
                    base_url=OLLAMA_BASE_URL
                )
                
            elif LLM_PROVIDER == 'openai':
                model = request.form.get('model', 'gpt-4o')
                logger.info(f"[OpenAI] Initializing with model: {model}")
                chat = ChatOpenAI(
                    model=model,
                    temperature=temp,
                    openai_api_key=OPENAI_API_KEY
                )
                
            elif LLM_PROVIDER == 'groq':
                logger.info("[Groq] Initializing ChatGroq instance...")
                chat = ChatGroq(
                    model="llama-3.3-70b-versatile",
                    temperature=temp,
                    api_key=GROQ_API_KEY
                )
            else:
                return jsonify({'error': f'Unknown LLM_PROVIDER: {LLM_PROVIDER}'}), 500
            
            if chat is None:
                return jsonify({'error': 'Failed to initialize LLM'}), 500
            
            # Extract text from document - verify file still exists
            if not os.path.exists(filepath):
                raise Exception(f"File was deleted before extraction: {filepath}")
            
            if filename.endswith('.docx') or filename.endswith('.doc'):
                extracted_text = extract_text_from_docx(filepath)
            else:
                with open(filepath, 'r', encoding='utf-8') as f:
                    extracted_text = f.read()
            
            # Process document using autoAgile
            mode = "prod"
            logger.info(f"Processing document: {filename}, length: {len(extracted_text)}")
            
            try:
                logger.info("STEP 1: Extracting requirements...")
                requirements = rat(refine_doc, extract_functionarity, extracted_text, chat, mode)
                
                if requirements is None:
                    raise Exception("Requirements extraction returned None")
                
                if not isinstance(requirements, str):
                    requirements = str(requirements)
                
                logger.info("Step 2: Extracting deliverables/epics...")
                # Use two-step process: extract deliverables, then refine with DoD
                deliverables = extract_epics(requirements, chat, mode)
                
                if deliverables is None:
                    raise Exception("Deliverables extraction returned None")
                if not isinstance(deliverables, str):
                    deliverables = str(deliverables)
                
                logger.info("Step 3: Refining epics with definition of done...")
                # Refine deliverables to add definition of done (get_epics)
                epics = get_epics(deliverables, chat)
                
                if epics is None:
                    raise Exception("Epics refinement returned None")
                if not isinstance(epics, str):
                    epics = str(epics)
                
                logger.info("Step 4: Epics extracted and refined successfully")
                
                logger.info("Step 4: Generating test cases...")
                # Optimization: Call generate_test_cases directly
                test_cases = generate_test_cases(requirements, chat, mode)
                if test_cases is None:
                    raise Exception("Test cases generation returned None")
                if not isinstance(test_cases, str):
                    test_cases = str(test_cases)
                    
            except Exception as processing_error:
                logger.error(f"Error during processing: {processing_error}")
                logger.error(traceback.format_exc())
                raise
            
            # VALIDATION
            epics_validation = validate_output(epics, extracted_text)
            print_validation_report(epics_validation, "Epics/User Stories Validation")
            
            test_cases_validation = validate_output(test_cases, extracted_text)
            print_validation_report(test_cases_validation, "Test Cases Validation")
            
            completeness_validation = validate_requirements_completeness(requirements, epics)
            print_validation_report(completeness_validation, "Completeness Validation")
            
            # Log epics before conversion for debugging
            logger.info(f"[API] Epics length: {len(epics) if epics else 0}")
            logger.info(f"[API] Epics preview (first 500 chars): {str(epics)[:500] if epics else 'None'}")
            
            # Convert to frontend format
            stories = convert_stories_to_frontend_format(epics, test_cases, requirements)
            
            logger.info(f"[API] Converted stories count: {len(stories) if stories else 0}")
            
            if not stories or len(stories) == 0:
                logger.error("[API] ⚠️ WARNING: No stories generated after conversion!")
                logger.error(f"[API] Epics was: {epics[:1000] if epics else 'None'}")
                # Return error instead of empty success
                return jsonify({
                    'success': False,
                    'error': 'No user stories were generated. Please check the server logs for details.',
                    'stories': [],
                    'count': 0
                }), 500
            
            # Save output to JSON file
            output_file_path = None
            try:
                output_file_path = save_json_output(requirements, epics, test_cases, filepath)
                logger.info(f"Output saved to: {output_file_path}")
            except Exception as save_error:
                logger.warning(f"Could not save JSON output: {save_error}")
            
            return jsonify({
                'success': True,
                'stories': stories,
                'count': len(stories),
                'output_file': output_file_path
            })
            
        finally:
            # Clean up temporary file
            if os.path.exists(filepath):
                os.remove(filepath)
                
    except Exception as e:
        logger.error(f"Error generating stories: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': f'Error generating stories: {str(e)}',
            'details': traceback.format_exc().split('\n')[-5:]
        }), 500

@api_bp.route('/integrate-story', methods=['POST'])
@login_required
def integrate_story():
    """Integrate a single user story - save to json_output (requires authentication)"""
    try:
        data = request.json
        story_id = data.get('storyId')
        story_data = data.get('story')
        
        if not story_data:
            return jsonify({'error': 'Story data not provided'}), 400
        
        # Save integrated story to json_output
        # We need to find where autoAgile is. Assuming it's in the project root.
        # current_app.root_path should point to where app.py is.
        output_dir = os.path.join(current_app.root_path, "autoAgile", "json_output")
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, mode=0o777, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(output_dir, f"integrated_story_{story_id}_{timestamp}.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'story_id': story_id,
                'integrated_at': timestamp,
                'story': story_data
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Integrated story {story_id} saved to: {output_file}")
        
        return jsonify({
            'success': True,
            'message': f'Story {story_id} integrated successfully',
            'storyId': story_id,
            'output_file': output_file
        })
    except Exception as e:
        logger.error(f"Error integrating story: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': f'Error integrating story: {str(e)}',
            'details': traceback.format_exc().split('\n')[-5:]
        }), 500

@api_bp.route('/integrate-all', methods=['POST'])
@login_required
def integrate_all():
    """Integrate all user stories - save to json_output (requires authentication)"""
    try:
        data = request.json
        story_ids = data.get('storyIds', [])
        stories_data = data.get('stories', [])
        
        if not stories_data:
            return jsonify({'error': 'Stories data not provided'}), 400
        
        output_dir = os.path.join(current_app.root_path, "autoAgile", "json_output")
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, mode=0o777, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(output_dir, f"integrated_all_stories_{timestamp}.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'integrated_at': timestamp,
                'total_stories': len(stories_data),
                'story_ids': story_ids,
                'stories': stories_data
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Integrated {len(stories_data)} stories saved to: {output_file}")
        
        return jsonify({
            'success': True,
            'message': f'All {len(story_ids)} stories integrated successfully',
            'storyIds': story_ids,
            'output_file': output_file
        })
    except Exception as e:
        logger.error(f"Error integrating all stories: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': f'Error integrating stories: {str(e)}',
            'details': traceback.format_exc().split('\n')[-5:]
        }), 500

@api_bp.route('/export-json', methods=['POST'])
@login_required
def export_json():
    """Export user stories as JSON file (requires authentication)"""
    try:
        data = request.json
        stories = data.get('stories', [])
        
        if not stories:
            return jsonify({'error': 'No stories provided'}), 400
        
        # Create JSON export
        from flask import send_file
        import io
        
        export_data = {
            'exported_at': datetime.now().isoformat(),
            'user': current_user.email,
            'total_stories': len(stories),
            'stories': stories
        }
        
        # Create in-memory file
        json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
        json_bytes = json_str.encode('utf-8')
        json_io = io.BytesIO(json_bytes)
        json_io.seek(0)
        
        filename = f"user_stories_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        return send_file(
            json_io,
            mimetype='application/json',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Error exporting to JSON: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': f'Error exporting to JSON: {str(e)}'
        }), 500

@api_bp.route('/export-docx', methods=['POST'])
@login_required
def export_docx():
    """Export user stories as Word document (requires authentication)"""
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor, Inches
        from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
        from flask import send_file
        import io
        
        data = request.json
        stories = data.get('stories', [])
        
        if not stories:
            return jsonify({'error': 'No stories provided'}), 400
        
        # Create Word document
        doc = Document()
        
        # Add title
        title = doc.add_heading('User Stories', 0)
        title.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        
        # Add metadata
        meta = doc.add_paragraph()
        meta.add_run(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n").bold = True
        meta.add_run(f"Total Stories: {len(stories)}\n").bold = True
        meta.add_run(f"User: {current_user.email}").bold = True
        
        doc.add_paragraph()  # Spacing
        
        # Add each story
        for idx, story in enumerate(stories, 1):
            # Story number heading
            story_heading = doc.add_heading(f"User Story {idx}", level=1)
            story_heading.runs[0].font.color.rgb = RGBColor(0, 122, 255)
            
            # Title
            if story.get('title'):
                title_para = doc.add_paragraph()
                title_para.add_run('Title: ').bold = True
                title_para.add_run(story['title'])
            
            # Description
            if story.get('description'):
                desc_para = doc.add_paragraph()
                desc_para.add_run('Description: ').bold = True
                desc_para.add_run(story['description'])
            
            # Definition of Done
            if story.get('definitionOfDone'):
                dod_para = doc.add_paragraph()
                dod_para.add_run('Definition of Done: ').bold = True
                dod_para.add_run(story['definitionOfDone'])
            
            # Test Cases
            if story.get('testCases'):
                tc_para = doc.add_paragraph()
                tc_para.add_run('Test Cases: ').bold = True
                tc_para.add_run(str(story['testCases']))
            
            # Add separator between stories
            if idx < len(stories):
                doc.add_paragraph('_' * 80)
        
        # Save to in-memory file
        docx_io = io.BytesIO()
        doc.save(docx_io)
        docx_io.seek(0)
        
        filename = f"user_stories_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        
        return send_file(
            docx_io,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Error exporting to DOCX: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': f'Error exporting to DOCX: {str(e)}'
        }), 500
