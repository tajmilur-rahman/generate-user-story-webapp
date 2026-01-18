import os
import unicodedata
import json
import logging
from docx import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_openai import ChatOpenAI, OpenAI
from langchain_ollama import ChatOllama

# Initialize logger
logger = logging.getLogger(__name__)

#set env variable auth_key to be the key
output_parser = StrOutputParser()
threshold = 5

def clean_json_response(text: str) -> str:
    """Clean LLM response to extract JSON content"""
    if not text or not text.strip():
        return "{}"
    
    # Remove markdown code blocks
    text = text.replace("```json", "").replace("```", "")
    text = text.replace("json", "", 1)  # Remove first occurrence only
    
    # Try to find JSON object boundaries
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        text = text[start_idx:end_idx + 1]
    
    return text.strip()

def safe_json_loads(text: str, default=None):
    """Safely parse JSON with error handling"""
    if default is None:
        default = {}
    
    if not text or not text.strip():
        return default
    
    try:
        cleaned = clean_json_response(text)
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Problematic text: {text[:200]}")
        # Try to fix common issues
        try:
            # Remove trailing commas
            cleaned = cleaned.replace(',\n}', '\n}').replace(',\n]', '\n]')
            return json.loads(cleaned)
        except:
            return default

def extract_text_from_docx(docx_path):
    doc = Document(docx_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def clean_doc(doc_text:str, chat)->str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a document refinement expert. Your task is to clean and improve the input document for better requirements extraction.

PROCESS:
1. Remove meaningless words, typos, and formatting artifacts
2. Correct grammar and spelling mistakes
3. Preserve all technical content, requirements, and functional descriptions
4. Improve clarity while maintaining original meaning
5. Organize content logically if it's scattered
6. Remove redundant sentences but keep all unique information

CRITICAL RULES:
- DO NOT remove any functional requirements or technical specifications
- DO NOT change the meaning of any requirement
- DO NOT add new information not in the original
- DO NOT summarize - keep all details
- Preserve all numbers, measurements, and technical terms exactly

OUTPUT: Return the cleaned document with improved formatting and clarity, but with ALL original content preserved."""),
        ("user", "{input}")
    ])
    chain = prompt | chat | output_parser
    re = chain.invoke({"input": doc_text})
    return re

def summarize_doc(doc_text:str, chat)->str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a software project manager. Please extract the text that describes the application we need
         to build the input document. Your summary should focused on the functional requirements.""")
        ,
        ("user", "{input}")
    ])
    chain = prompt | chat | output_parser
    re = chain.invoke({"input": doc_text})
    return re

def refine_doc(doc_text: str, chat, mode)->str:
    cleaned = clean_doc(doc_text, chat)
    #re = summarize_doc(cleaned, chat)
    return cleaned

def extract_list(doc_text:str,chat)->str:
    """Extract requirements list from document text using LLM."""
    try:
        if not doc_text or not doc_text.strip():
            print("[ERROR] extract_list called with empty document text")
            return '{"requirements": []}'
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a software engineer developing functional requirements from a software product design document.

YOUR TASK: Extract the list of functional requirements from the given document.

REQUIREMENTS:
1. Extract ALL functional requirements that describe what the system must do
2. Integration testing is always one of the requirements
3. Focus on the PRIMARY TARGET SYSTEM (not management/monitoring systems)
4. Each requirement should be clear and specific

OUTPUT FORMAT:
Return as a numbered list of functional requirements, one per line.

Example:
1. The system must collect temperature and pressure data from sensors.
2. The system must process and aggregate data locally.
3. The system must transmit data via satellite communication.
4. The system must store data locally when communication is unavailable.
5. Integration testing must verify all components work together.

Return ONLY the list of requirements. No explanations, no markdown formatting.""")
            ,
            ("user", "{input}")
        ])
        chain = prompt | chat | output_parser
        
        print("[INFO] Invoking LLM for requirement extraction...")
        re = chain.invoke({"input": doc_text})
        
        if re is None:
            print("[ERROR] extract_list LLM call returned None")
            return '{"requirements": []}'
        
        if not re.strip():
            print("[ERROR] extract_list LLM call returned empty string")
            return '{"requirements": []}'
        
        print(f"[OK] extract_list succeeded, returned {len(re)} characters")
        return re
        
    except Exception as e:
        print(f"[ERROR] extract_list failed: {e}")
        import traceback
        traceback.print_exc()
        # Return empty requirements instead of raising to allow retry
        return '{"requirements": []}'

def compare_answer(answer_left, answer_right,chat)->bool:
    prompt = (PromptTemplate.from_template("""Please compare the two input software requirement lists and determine whether\n                                            they are describing the same list of requirements. Given the first list:\n\n                                         {input_first}\n and the second:\n {input_second}\n, are they describing the\n                                            same requirements? Please provide reasoning steps in your answer, also with\n                                            keyword yes indicating they are the same or no indicating they are not the\n                                            same."""))
    
    chain = prompt | chat | output_parser
    re_text = chain.invoke({"input_first":answer_left, "input_right":answer_right})
    print("=============================\n")
    print(re_text) 
    print("=============================\n")
    return ("yes" in re_text.lower())

def self_consistency(answers: list[str], chat)->str:
    votes = {answers[0]: 1} 
    find = False
    for answer in answers[1:]:
        for k in votes.keys():
            if compare_answer(k, answer, chat):
                votes[k] +=1
                find = True
                break
        if not find:
            votes[answer] = 1
            find = False
    print(votes)
    result = max(votes, key=votes.get)
    print(result)
    return result

def rank_answer(answer_left, answer_right,chat, mode="debug")->str:
    """Rank two answers and return the better one. Returns answer_left as fallback if ranking fails."""
    try:
        prompt = (PromptTemplate.from_template("""As a software developer, you vote for the software requirement list that is more detailed and specific.\n\nGiven two input texts, the first:\n\n{input_first}\n and the second:\n {input_second}\n, which one you vote for?\nPlease only answer with your vote."""))
        
        chain = prompt | chat | output_parser
        better = answer_left  # Default fallback
        re_text = chain.invoke({"input_first":answer_left, "input_second":answer_right})
        if '1' in re_text.lower() or 'first' in re_text.lower():
            better = answer_left
        elif '2' in re_text.lower() or "second" in re_text.lower():
            better = answer_right
        if mode == "debug":
            print("=============================\n")
            print(re_text)
            print("===========the better result is=========\n")
            print(better)
            print("=============================\n")
        return better
    except Exception as e:
        print(f"[WARNING] rank_answer failed: {e}, using first answer as fallback")
        # Return the first answer as fallback if ranking fails
        return answer_left

def c_o_t(answers: list[str], chat, mode="debug")->str:
    """Chain of thought: rank multiple answers and return the best one."""
    if not answers:
        raise Exception("c_o_t called with empty answers list")
    
    if len(answers) == 1:
        print("[INFO] Only one answer, using it directly (no need to rank)")
        return answers[0]
    
    better = answers[0]
    for i, answer in enumerate(answers[1:], 1):
        try:
            better = rank_answer(better, answer, chat, mode)
            if better is None:
                print(f"[WARNING] rank_answer returned None for comparison {i}, keeping previous result")
                better = answers[0]  # Fallback to first answer
        except Exception as e:
            print(f"[WARNING] rank_answer failed for comparison {i}: {e}, keeping previous result")
            # Continue with current 'better' value
    
    if better is None or not better.strip():
        print("[WARNING] c_o_t result is None or empty, using first answer as fallback")
        better = answers[0]
    
    return better

def extract_functionarity(doc_text:str,chat, mode="debug")->str:
    """Extract requirements from document text using multiple attempts and consolidation."""
    try:
        if not doc_text or not doc_text.strip():
            raise Exception("Document text is empty or None")
        
        print(f"[INFO] Starting requirement extraction (mode: {mode})")
        print(f"[INFO] Document text length: {len(doc_text)} characters")
        
        requirements = []
        successful_attempts = 0
        
        for i in range(threshold):
            try:
                print(f"[INFO] Attempt {i+1}/{threshold} to extract requirements...")
                req = extract_list(doc_text, chat)
                if req and req.strip():
                    requirements.append(req)
                    successful_attempts += 1
                    print(f"[OK] Attempt {i+1} succeeded, extracted {len(req)} characters")
                else:
                    print(f"[WARNING] extract_list attempt {i+1} returned empty, skipping")
            except Exception as e:
                print(f"[WARNING] extract_list attempt {i+1} failed: {e}, continuing...")
                import traceback
                if mode == "debug":
                    traceback.print_exc()
                continue
        
        if not requirements:
            print("[ERROR] All extract_list attempts failed or returned empty")
            raise Exception("Failed to extract any requirements from document after all attempts")
        
        print(f"[OK] Successfully extracted requirements from {successful_attempts}/{threshold} attempts")
        print(f"[INFO] Consolidating {len(requirements)} requirement extractions...")
        
        try:
            result = c_o_t(requirements, chat, mode)
            if result is None or not result.strip():
                print("[ERROR] c_o_t returned None or empty")
                # Fallback: use the first successful extraction
                if requirements:
                    print("[FALLBACK] Using first successful extraction as result")
                    result = requirements[0]
                else:
                    raise Exception("Failed to consolidate requirements and no fallback available")
            
            print(f"[OK] Requirements consolidated successfully, result length: {len(result)} characters")
            return result
        except Exception as e:
            print(f"[ERROR] c_o_t failed: {e}")
            # Fallback: use the first successful extraction
            if requirements:
                print("[FALLBACK] Using first successful extraction as result due to consolidation failure")
                return requirements[0]
            else:
                raise Exception(f"Failed to consolidate requirements: {str(e)}") from e
    
    except Exception as e:
        print(f"[ERROR] extract_functionarity failed: {e}")
        import traceback
        traceback.print_exc()
        raise Exception(f"Failed to extract functionality: {str(e)}") from e

def refine_requirements(requirements:str,chat,mode)->str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a project manager refining functional requirements.

YOUR TASK: Refine the given functional requirements by:
1. Combining redundant requirements
2. Adding missing requirements that are necessary based on existing ones
3. Making requirements clear and specific

GUIDELINES:
- Consolidate duplicates and overlaps
- Add necessary requirements that are implied but missing
- Keep requirements clear, specific, and actionable
- Maintain numbered list format

OUTPUT FORMAT:
Return as a clean numbered list of refined functional requirements, one per line.

Example:
1. The system must collect temperature and pressure data from sensors.
2. The system must process and aggregate data locally before transmission.
3. The system must transmit data via satellite communication.
4. The system must store data locally when communication is unavailable.

Return ONLY the refined requirements list. No explanations, no markdown formatting.""")
        ,
        ("user", "{input}")
    ])
    chain = prompt | chat | output_parser
    re = chain.invoke({"input": requirements})
    return re
def get_epics(deliverables: str, chat) -> str:
    """
    Convert deliverables to user stories by adding definition of done for each deliverable.
    This is a two-step process: first extract deliverables, then refine with DoD.
    """
    try:
        logger.info(f"[get_epics] Starting with deliverables (length: {len(deliverables) if deliverables else 0})")
        
        # Clean the deliverables string first
        cleaned = clean_json_response(deliverables)
        just_tasks = json.loads(cleaned)
        
        logger.info(f"[get_epics] Parsed JSON, keys: {list(just_tasks.keys())}")
        
        _key = "Epics"
        new_key = "User Stories"
        _key_2 = "Deliverables"
        refine_tasks = {new_key: []}
        
        epics_list = just_tasks.get(_key, [])
        logger.info(f"[get_epics] Found {len(epics_list)} epics to process")
        
        if not epics_list:
            logger.warning(f"[get_epics] No epics found in deliverables! Available keys: {list(just_tasks.keys())}")
            logger.warning(f"[get_epics] Full deliverables structure: {json.dumps(just_tasks, indent=2)[:1000]}")
            
            # Try alternative: maybe it's already in "User Stories" format
            if "User Stories" in just_tasks:
                logger.info(f"[get_epics] Found 'User Stories' key, using it directly")
                return json.dumps(just_tasks, indent=4)
            
            # Try to return what we have, but log the issue
            logger.error(f"[get_epics] ⚠️ CRITICAL: No epics to process! Returning empty list")
            return json.dumps({new_key: []}, indent=4)
        
        for idx, epic in enumerate(epics_list):
            try:
                logger.info(f"[get_epics] Processing epic {idx + 1}/{len(epics_list)}")
                logger.info(f"[get_epics] Epic structure: {json.dumps(epic, indent=2)[:500]}")
                
                # Check if epic already has Deliverables with definitionOfDone
                if _key_2 in epic and isinstance(epic[_key_2], dict):
                    # Check if deliverables already have definitionOfDone
                    has_dod = any(
                        isinstance(v, dict) and "definitionOfDone" in v 
                        for v in epic[_key_2].values()
                    )
                    if has_dod:
                        logger.info(f"[get_epics] Epic {idx + 1} already has DoD, skipping refine_epics")
                        refine_tasks[new_key].append(epic)
                        continue
                
                # Refine each epic to add definition of done
                refined_result = refine_epics(json.dumps(epic), chat)
                logger.info(f"[get_epics] Refined result length: {len(refined_result) if refined_result else 0}")
                
                new_devs = json.loads(clean_json_response(refined_result))
                logger.info(f"[get_epics] Parsed new_devs, keys: {list(new_devs.keys()) if isinstance(new_devs, dict) else 'not a dict'}")
                
                # Merge new_devs into existing Deliverables or replace
                if _key_2 in epic and isinstance(epic[_key_2], dict):
                    # Merge: update existing deliverables with DoD
                    for k, v in new_devs.items():
                        if isinstance(v, dict):
                            epic[_key_2][k] = v
                        else:
                            epic[_key_2][k] = {"definitionOfDone": str(v)}
                else:
                    # Replace: set Deliverables to new_devs
                    epic[_key_2] = new_devs
                
                refine_tasks[new_key].append(epic)
                logger.info(f"[get_epics] Successfully processed epic {idx + 1}")
            except Exception as epic_error:
                logger.error(f"[get_epics] Error processing epic {idx + 1}: {epic_error}")
                import traceback
                logger.error(traceback.format_exc())
                # Continue with other epics even if one fails - include epic with empty DoD
                if _key_2 not in epic:
                    epic[_key_2] = {}
                refine_tasks[new_key].append(epic)
        
        epics = json.dumps(refine_tasks, indent=4)
        logger.info(f"[get_epics] Successfully processed {len(refine_tasks[new_key])} user stories")
        return epics
    except Exception as e:
        logger.error(f"Error in get_epics: {e}")
        import traceback
        traceback.print_exc()
        # Fallback: return deliverables as-is, but try to convert format
        try:
            cleaned = clean_json_response(deliverables)
            just_tasks = json.loads(cleaned)
            if "Epics" in just_tasks:
                # Convert Epics to User Stories format
                return json.dumps({"User Stories": just_tasks["Epics"]}, indent=4)
        except:
            pass
        return deliverables

def extract_epics(requirements: str, chat, mode) -> str:
    """Extract epics (user stories) from the given requirements.

    Args:
        requirements: Source text containing requirements.
        chat: LLM chat model.
        mode: Execution mode (e.g., "prod" or "debug").

    Returns:
        A JSON string with extracted epics.
    """
    pp = """You are a product manager creating deliverables from software requirements. 
Generate deliverables that can be assigned to developers for each functional requirement.

CRITICAL: You MUST return valid JSON with the exact structure shown below.

TASK: For each requirement in the input, create ONE epic with:
1. A User Story describing what the system must do
2. At least one deliverable that needs to be built

DELIVERABLES OPTIONS (select 1-3 per requirement based on what's needed):
- architecture_design: System architecture and component design
- database_schema_design: Database structure and schema  
- unit_tests: Unit test specifications
- user_training_documentation: User training materials
- production_support_plan: Production deployment and support plan

REQUIRED OUTPUT FORMAT (JSON - MUST FOLLOW EXACTLY):
{{
  "Epics": [
    {{
      "User Story": "The system must [ACTION] so that [BUSINESS VALUE]",
      "Deliverables": {{
        "architecture_design": "Description of what needs to be delivered"
      }}
    }},
    {{
      "User Story": "The system must [ANOTHER ACTION] so that [ANOTHER VALUE]",
      "Deliverables": {{
        "database_schema_design": "Description of database design needed"
      }}
    }}
  ]
}}

RULES:
1. Create ONE epic per requirement in the input
2. Each epic MUST have "User Story" and "Deliverables" fields
3. User Story format: "The system must [action] so that [value]"
4. Deliverables must be a dictionary with at least one deliverable
5. Focus on the PRIMARY TARGET SYSTEM (not management/monitoring systems)
6. Extract ALL requirements - don't skip any

EXAMPLE OUTPUT:
{{
  "Epics": [
    {{
      "User Story": "The system must collect temperature data from sensors so that accurate weather information is available",
      "Deliverables": {{
        "architecture_design": "Design sensor data collection module with error handling"
      }}
    }},
    {{
      "User Story": "The system must transmit data via satellite so that information reaches the central server",
      "Deliverables": {{
        "architecture_design": "Design satellite communication module with retry logic"
      }}
    }}
  ]
}}

VALIDATION CHECKLIST:
- [ ] JSON is valid (can be parsed)
- [ ] "Epics" key exists
- [ ] At least one epic in the array
- [ ] Each epic has "User Story" field
- [ ] Each epic has "Deliverables" field
- [ ] Deliverables is a dictionary (not a string)

Return ONLY valid JSON matching the format above. NO markdown, NO explanations, NO code blocks."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", pp),
        ("user", "{input}")
    ])
    chain = prompt | chat | output_parser
    re = chain.invoke({"input": requirements})
    logger.info(f"[extract_epics] Raw response length: {len(re) if re else 0}")
    
    # Clean and return the response
    cleaned = clean_json_response(re)
    logger.info(f"[extract_epics] Cleaned response length: {len(cleaned)}")
    
    try:
        parsed = json.loads(cleaned)
        logger.info(f"[extract_epics] Valid JSON, keys: {list(parsed.keys()) if isinstance(parsed, dict) else 'not a dict'}")
        if isinstance(parsed, dict):
            epics_count = len(parsed.get("Epics", []))
            logger.info(f"[extract_epics] Found {epics_count} epics in response")
        return cleaned
    except json.JSONDecodeError as e:
        logger.warning(f"Warning: Invalid JSON from extract_epics: {e}")
        logger.warning(f"Cleaned response (first 500 chars): {cleaned[:500]}")
        return cleaned
def refine_epics(epic:str,chat)->str:
    """
    Refine an epic by adding definition of done for each deliverable.
    This is called by get_epics() to add DoD criteria to deliverables.
    """
    pp = """You are refining deliverables by adding definition of done criteria for each deliverable.

TASK: For each deliverable in the epic, generate a clear definition of done that specifies what "done" means.

REQUIREMENTS:
- Criteria should be specific, measurable, and testable
- Focus on quality and completeness indicators
- Based on the user story and deliverable description
- Use qualitative terms from source: "successfully", "reliably", "efficiently"
- DO NOT invent metrics, percentages, or time windows

OUTPUT FORMAT (JSON):
{{
  "deliverable_name": {{
    "definitionOfDone": "Specific, measurable criteria for completion"
  }},
  "another_deliverable": {{
    "definitionOfDone": "Specific criteria for this deliverable"
  }}
}}

EXAMPLE:
{{
  "architecture_design": {{
    "definitionOfDone": "The architecture design document includes: system components diagram, data flow diagrams, interface specifications, and technology stack decisions. All components are documented with their responsibilities and interactions."
  }},
  "database_schema_design": {{
    "definitionOfDone": "The database schema includes: all required tables with relationships, indexes for performance, data validation rules, and migration scripts. Schema is reviewed and approved."
  }}
}}

Return ONLY valid JSON matching the structure above. No markdown, no explanations."""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", pp),
        ("user", "{input}")
    ])
    chain = prompt | chat | output_parser
    re = chain.invoke({"input": epic})
    logger.info(f"[refine_epics] Raw response length: {len(re) if re else 0}")
    
    cleaned = clean_json_response(re)
    logger.info(f"[refine_epics] Cleaned response: {cleaned[:500]}")
    
    # Validate it's valid JSON
    try:
        parsed = json.loads(cleaned)
        logger.info(f"[refine_epics] Valid JSON, keys: {list(parsed.keys()) if isinstance(parsed, dict) else 'not a dict'}")
        return cleaned
    except json.JSONDecodeError as e:
        logger.warning(f"[refine_epics] Invalid JSON: {e}, returning cleaned version anyway")
        return cleaned

def generate_test_cases(requirements:str,chat, mode)->str:
    pp = """You are a QA engineer generating test cases from software requirements.

YOUR TASK: Generate test cases for each requirement that can be used to verify the completeness of those requirements.

REQUIREMENTS:
1. Create test cases for EACH requirement
2. Test cases should be specific and concrete (not generic templates)
3. Include normal cases and edge cases
4. Use concrete input/output data with actual values

OUTPUT FORMAT (JSON):
{{
  "testCases": [
    {{
      "requirement_id": 1,
      "scenarios": [
        {{
          "name": "Test [specific scenario]",
          "input": {{
            "field1": "concrete_value",
            "field2": "concrete_value"
          }},
          "expected_output": {{
            "field1": "expected_value",
            "status": "success"
          }}
        }}
      ]
    }}
  ]
}}

RULES:
- NO generic templates like "Verify that the system must [requirement]"
- NO vague outputs like "data" or "success" - be specific
- Use concrete values and data structures
- Include edge cases and error scenarios
- One test case group per requirement

Return ONLY valid JSON. No markdown, no explanations."""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", pp),
        ("user", "{input}")
    ])
    chain = prompt | chat | output_parser
    re = chain.invoke({"input": requirements})
    cleaned = clean_json_response(re)
    # Validate it's valid JSON
    try:
        json.loads(cleaned)
        return cleaned
    except json.JSONDecodeError:
        print(f"Warning: Invalid JSON from generate_test_cases, returning cleaned version")
        return cleaned

def rat(refine, thought, x,chat, mode="prod"):
    prompt = (PromptTemplate.from_template("""As a voter, you vote for the input that is more accurate, concise and easy\n                                            to understand. Given two input texts, the first:\n\n                                         {input_first}\n and the second:\n {input_second}\n, which one you vote for?\n                                            Please only answer with your vote."""))
    
    try:
        x1 = refine(x, chat, mode)
        if x1 is None:
            print("[WARNING] refine() returned None, using original input")
            x1 = x
    except Exception as refine_error:
        print(f"[WARNING] refine() failed: {refine_error}, using original input")
        import traceback
        traceback.print_exc()
        x1 = x
    
    if mode == "debug":
        print("Refine successfully:\n")
        print("=============================\n")
        print(x1)
        print("=============================\n")
    
    try:
        chain = prompt | chat | output_parser
        better = None
        re_text = chain.invoke({"input_first": x, "input_second": x1})
        if mode == "debug":
            print(re_text)
        if '1' in re_text.lower() or 'first' in re_text.lower():
            better = x
        elif '2' in re_text.lower() or "second" in re_text.lower():
            better = x1
        else:
            # Default to refined version if unclear
            better = x1
    except Exception as vote_error:
        print(f"[WARNING] Voting failed: {vote_error}, using refined version")
        import traceback
        traceback.print_exc()
        better = x1
    
    try:
        x2 = thought(better, chat, mode)
        if x2 is None:
            print("[ERROR] thought() returned None - LLM call may have failed")
            raise Exception("LLM extraction function returned None")
        return x2
    except Exception as thought_error:
        print(f"[ERROR] thought() failed: {thought_error}")
        import traceback
        traceback.print_exc()
        raise Exception(f"LLM extraction failed: {str(thought_error)}") from thought_error
