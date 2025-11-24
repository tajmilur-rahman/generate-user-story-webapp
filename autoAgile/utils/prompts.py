import os
import unicodedata
import json
from docx import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_openai import ChatOpenAI, OpenAI
from langchain_ollama import ChatOllama

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
        ("system", """You are an assistant that help improve the input document. You will correct grammar mistakes,
         remove meaningless words or characters from the input document and improve its formatting."""),
        ("user", "{input}")
    ])
    chain = prompt | chat | output_parser
    re = chain.invoke({"input": doc_text})
    return re

def summarize_doc(doc_text:str, chat)->str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a software project manager. Please extract the text that describes the application we need
         to build the input document. Your summary should focused on the functional requirements."""),
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
            ("system", """You are a requirements extraction system. Extract user stories, deliverables, and test cases from the provided source text.

CRITICAL RULES:

1. ONLY extract requirements EXPLICITLY stated in the source text
2. DO NOT infer, assume, or add requirements based on best practices
3. DO NOT add features common to other systems (auth, search, profiles, etc.)
4. If functionality is not mentioned in the source, DO NOT include it
5. Every requirement must have a direct quote from the source as evidence

EXTRACTION PROCESS:

Step 1: Extract Requirements
- Read the source text carefully
- Identify each distinct functional requirement
- Look for ALL major functionalities:
  * Data collection and processing
  * Communication methods (satellite, radio, etc.)
  * Storage mechanisms (local storage, data aggregation)
  * Failure handling (backup instruments, recovery processes)
  * Power management (battery charging, generator control)
  * System reconfiguration capabilities
  * Self-contained operation features
- For each requirement, capture:
  * Brief requirement statement (5-10 words)
  * Direct quote from source text as evidence
  * Confidence level (high/medium/low)
- Don't just extract bullet points - extract contextual capabilities too

OUTPUT FORMAT:

{{
  "requirements": [
    {{
      "id": 1,
      "statement": "brief requirement",
      "source_quote": "exact text from source",
      "confidence": "high"
    }}
  ]
}}

EXAMPLES OF WHAT NOT TO DO:
❌ Adding authentication when source doesn't mention it
❌ Adding user profiles when source doesn't mention them
❌ Adding search when source doesn't mention it
❌ Changing "automatic transmission" to "user uploads"
❌ Inventing metrics like "24 hours" when not in source

EXAMPLES OF WHAT TO DO:
✅ Only include features explicitly in source text
✅ Quote source text as evidence for each requirement

Return ONLY valid JSON, no markdown, no explanations."""),
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
    prompt = (PromptTemplate.from_template("""Please compare the two input software requirement lists and determine whether
                                           they are describing the same list of requirements. Given the first list:\n
                                        {input_first}\n and the second:\n" {input_second}\n", are they describing the
                                           same requirements? Please provide reasoning steps in your answer, also with
                                           keyword yes indicating they are the same or no indicating they are not the
                                           same."""))

    chain = prompt | chat | output_parser
    re_text = chain.invoke({"input_first":answer_left, "input_second":answer_right})
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
        prompt = (PromptTemplate.from_template("""As a software developer, you vote for the software requirement list that is more detailed and specific.\n
                                               \nGiven two input texts, the first:\n
                                            {input_first}\n and the second:\n" {input_second}\n", which one you vote for?
                                               Please only answer with your vote."""))

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
        # Only one answer, return it directly (no need to rank)
        print("[INFO] Only one requirement extraction succeeded, using it directly")
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
        ("system", """You are a senior project manager refining functional requirements.

PRIMARY GOAL: Reduce the number of requirements by consolidating related items while maintaining quality.

Your task:
1. CONSOLIDATE: Combine redundant or overlapping requirements into single, comprehensive statements
2. ELIMINATE: Remove duplicate or near-duplicate requirements
3. GROUP: Organize requirements by capability domain (authentication, search, navigation, data management, etc.)
4. CLARIFY: Make requirements clear, specific, and actionable
5. REDUCE: Aim for 10-20 high-quality requirements total, NOT 50+
5. Group related requirements logically
6. Ensure integration testing is included

Guidelines:
- Remove duplicates and merge similar requirements
- Add missing requirements that are necessary for system completeness
- Keep requirements clear, specific, and measurable
- Maintain the numbered list format

Return as a clean numbered list, one requirement per line."""),
        ("user", "{input}")
    ])
    chain = prompt | chat | output_parser
    re = chain.invoke({"input": requirements})
    return re

def extract_epics(requirements:str,chat, mode)->str:
    pp = """You are a requirements extraction system. Extract user stories, deliverables, and test cases from the provided source text.

🚨 CRITICAL: SYSTEM BOUNDARY ENFORCEMENT 🚨

The source text may describe MULTIPLE systems. You MUST identify which system each requirement belongs to and ONLY extract requirements for the PRIMARY TARGET SYSTEM.

COMMON SYSTEM TYPES IN SOURCE TEXTS:
1. **Individual Component System** (e.g., "Weather Station System") - ONE instance doing its job
   - Example: "The weather station collects data" → EXTRACT THIS
   - Example: "The station processes data locally" → EXTRACT THIS

2. **Aggregation/Management System** (e.g., "Data Management System") - Collects from MULTIPLE instances
   - Example: "The system collects data from ALL weather stations" → DO NOT EXTRACT (wrong system)
   - Example: "The system archives data for other systems" → DO NOT EXTRACT (wrong system)
   - Keywords: "all stations", "multiple", "aggregates from", "collects from all"

3. **Monitoring/Maintenance System** (e.g., "Station Maintenance System") - Monitors MULTIPLE instances
   - Example: "The system monitors ALL weather stations" → DO NOT EXTRACT (wrong system)
   - Example: "The system provides reports of problems across stations" → DO NOT EXTRACT (wrong system)
   - Keywords: "monitors stations", "reports problems", "remote control of stations"

EXTRACTION RULES:
✅ EXTRACT: Requirements describing what ONE instance of the target system does
✅ EXTRACT: Self-contained operations (collects, processes, stores, manages its own resources)
❌ DO NOT EXTRACT: Requirements about "all instances" or "multiple instances"
❌ DO NOT EXTRACT: Requirements about collecting from other systems
❌ DO NOT EXTRACT: Requirements about monitoring other systems
❌ DO NOT EXTRACT: Requirements about archiving for other systems

VALIDATION CHECK:
Before including a requirement, ask: "Does this describe what ONE instance does, or what a system managing MULTIPLE instances does?"
- If ONE instance → EXTRACT
- If MULTIPLE instances → SKIP (wrong system)

CRITICAL RULES:

1. ONLY extract requirements EXPLICITLY stated in the source text
2. DO NOT infer, assume, or add requirements based on best practices
3. DO NOT add features common to other systems (auth, search, profiles, etc.)
4. If functionality is not mentioned in the source, DO NOT include it
5. Every requirement must have a direct quote from the source as evidence
6. ONLY extract requirements for the PRIMARY TARGET SYSTEM (not aggregation/monitoring systems)

ZERO TOLERANCE FOR HALLUCINATIONS:

FORBIDDEN FEATURES (Never extract these unless explicitly in source):
❌ Authentication systems (login, passwords, 2FA, OAuth, user accounts)
❌ User management (profiles, accounts, permissions, roles, access control)
❌ Search functionality (unless source explicitly describes search requirements)
❌ Notification systems (email, SMS, push notifications, alerts)
❌ Admin panels or dashboards (unless source explicitly describes them)
❌ Reporting features (unless source explicitly describes reporting requirements)
❌ API endpoints or web services (unless source explicitly describes APIs)
❌ Social features (comments, likes, sharing, following)
❌ Gamification (badges, points, leaderboards)
❌ Analytics or tracking (unless source explicitly requires it)

EXTRACTION PROCESS - MANDATORY STEPS:
1. Read source text completely
2. For EACH potential requirement:
   a. Find EXACT quote proving it exists
   b. Copy quote verbatim (no paraphrasing)
   c. If no quote found → SKIP this requirement
   d. If uncertain → SKIP this requirement
3. Double-check: Does this quote exist in the source?
4. If answer is NO → DELETE this requirement

VERIFICATION BEFORE OUTPUT:
Before including ANY story, ask yourself:
- "Can I point to specific text in the source that describes this?"
- "Is this feature actually mentioned, or am I assuming it's needed?"
- "Would someone reading only the source text expect this feature?"

If you answer NO to any question → DELETE that story.

REMEMBER: It's better to miss a real requirement than to invent a fake one.
When in doubt, LEAVE IT OUT.

ZERO TOLERANCE FOR INVENTED METRICS:
❌ NEVER add: percentages, time windows, success rates, specific numbers
❌ NEVER write: "90%", "2 hours", "30 transmissions", "80% of components", "within 5 minutes", "does not exceed 2 seconds"
✅ ONLY USE: qualitative terms from source text
✅ WRITE: "successfully", "reliably", "when conditions permit", "efficiently"

SOURCE QUOTE MANDATORY:
- Every requirement MUST include exact quote from source
- Every DoD statement MUST reference specific source text
- If you can't find a quote, don't include the metric

COMPLETENESS REQUIREMENT:
- Create ONE user story for EACH requirement (NO EXCEPTIONS)
- If input has N requirements, output MUST have N user stories
- Count requirements in input and ensure story count matches exactly
- Extract EVERY distinct function mentioned in source
- Missing functions = incomplete requirements

EXTRACTION PROCESS:

Step 2: Create User Stories
Format: "The system must [ACTION] so that [BUSINESS VALUE]"

Rules for "so that" clause:
- Must provide actual business benefit, NOT circular logic
- Must be based on source text context
- BAD: "collect data so that it can monitor hardware" (different functions)
- GOOD: "collect data so that weather conditions can be recorded"
- BAD: "monitor hardware so that it can detect failures" (circular)
- GOOD: "monitor hardware so that problems are identified before data loss"

Step 3: Define Deliverables
- Use unique, descriptive names (NO generic names like "Data Management")
- Base Definition of Done on source text details
- DO NOT invent metrics not in source (NO seconds, minutes, percentages, hours)
- Use qualitative terms: "efficiently", "quickly", "reliably", "successfully"
- BAD: "within 5 minutes", "does not exceed 2 seconds", "24 hours battery life", "90% success rate"
- GOOD: "successfully transmits aggregated data", "processes data efficiently", "maintains operation reliably"
- Include specific technical details from source (communication methods, storage mechanisms, failure handling)

EXTRACT ALL MAJOR FUNCTIONALITIES:
- Look for: communication methods (satellite, radio, etc.)
- Look for: storage mechanisms (local storage, data aggregation)
- Look for: failure handling (backup instruments, recovery processes)
- Look for: hardware monitoring and fault reporting
- Look for: power management (generator shutdown in high wind, battery charging)
- Look for: system reconfiguration (backup instrument failover, software updates)
- Don't just extract bullet points - extract contextual capabilities too

OUTPUT JSON:
{{
    "Epics": [
        {{
            "Title": "Short, descriptive title (3-5 words)",
            "User Story": "The system must [ACTION] so that [BUSINESS VALUE]",
            "source_quote": "exact quote from source text proving this requirement exists",
            "Deliverables": {{
                "Unique_Deliverable_Name": {{
                    "definition_of_done": "specific criteria from source (NO invented metrics, must reference source text)"
                }}
            }}
        }}
    ]
}}

VALIDATION CHECKLIST BEFORE OUTPUT:
- [ ] Count requirements in input
- [ ] Count user stories in output - MUST MATCH
- [ ] Check: no invented numbers (%, seconds, counts, time windows)
- [ ] All stories have source text basis with exact quotes
- [ ] All major functions from source are covered
- [ ] Verify: valid JSON structure (no nested string arrays, no malformed sections)

EXAMPLES OF WHAT NOT TO DO:
❌ Adding authentication when source doesn't mention it
❌ Adding user profiles when source doesn't mention them
❌ Adding search when source doesn't mention it
❌ Using "so that it can do X" when X is part of the requirement itself
❌ Inventing metrics like "24 hours", "5 minutes", "2 seconds", "90%", "30 transmissions" when not in source
❌ Creating fewer user stories than requirements
❌ Generic DoD statements without source reference

EXAMPLES OF WHAT TO DO:
✅ Only include features explicitly in source text
✅ Quote source text as evidence for each requirement
✅ User stories with clear business value: "so that weather forecasts are more accurate"
✅ ONE story per requirement (if 5 requirements, then 5 stories)
✅ Qualitative terms: "efficiently", "successfully", "reliably"
✅ DoD statements that reference specific source text

Return ONLY valid JSON, no markdown, no explanations.
        """
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
        print(f"Warning: Invalid JSON from extract_epics, returning cleaned version")
        return cleaned

def refine_epics(epic:str,chat)->str:
    pp = """You are refining an epic (user story) by adding detailed definition of done criteria for each deliverable.

For each deliverable in the epic, generate:
- A clear definition of done that specifies what "done" means for that deliverable
- Criteria should be specific, measurable, and testable
- Focus on quality and completeness indicators

Example format:
{{
    "architecture_design": {{
        "definition_of_done": "The architecture design document includes: system components diagram, data flow diagrams, interface specifications, and technology stack decisions. All components are documented with their responsibilities and interactions."
    }},
    "database_schema_design": {{
        "definition_of_done": "The database schema includes: all required tables with relationships, indexes for performance, data validation rules, and migration scripts. Schema is reviewed and approved by the database team."
    }}
}}

IMPORTANT: Return ONLY valid JSON matching the structure above, no markdown, no explanations."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", pp),
        ("user", "{input}")
    ])
    chain = prompt | chat | output_parser
    re = chain.invoke({"input": epic})
    cleaned = clean_json_response(re)
    # Validate it's valid JSON
    try:
        json.loads(cleaned)
        return cleaned
    except json.JSONDecodeError:
        print(f"Warning: Invalid JSON from refine_epics, returning cleaned version")
        return cleaned

def generate_test_cases(requirements:str,chat, mode)->str:
    pp = """You are a requirements extraction system. Extract user stories, deliverables, and test cases from the provided source text.

CRITICAL RULES:

1. ONLY extract requirements EXPLICITLY stated in the source text
2. DO NOT infer, assume, or add requirements based on best practices
3. DO NOT add features common to other systems (auth, search, profiles, etc.)
4. If functionality is not mentioned in the source, DO NOT include it
5. Every requirement must have a direct quote from the source as evidence

ZERO TOLERANCE FOR INVENTED METRICS:
❌ NEVER add: percentages, time windows, success rates, specific numbers
❌ NEVER write: "90%", "2 hours", "30 transmissions", "80% of components"
✅ ONLY USE: qualitative terms from source text

🚨 CRITICAL: TEST CASES MUST BE CONCRETE AND SPECIFIC 🚨

ZERO TOLERANCE FOR TEMPLATE TEST CASES:
❌ NEVER write: "Verify that the system must [requirement]"
❌ NEVER write: "Functionality works as specified"
❌ NEVER write: "Functionality works as specified in the user story"
❌ NEVER write: "Test cases will be defined during test planning"
❌ NEVER write: Generic test outputs like "weather_data", "data", "result"
❌ NEVER write: Vague expected outputs without concrete values
✅ ALWAYS write: Specific input data with concrete values + Expected output data with concrete values
✅ ALWAYS write: Test names that describe the specific scenario being tested
✅ ALWAYS write: Expected outputs with actual data types, formats, and example values

TEMPLATE DETECTION - IF YOU SEE THESE PATTERNS, YOU'RE WRONG:
- "Verify that the system must..." → WRONG (template)
- "Functionality works as specified" → WRONG (template)
- "Test: [requirement copy-paste]" → WRONG (template)
- Expected: "weather_data" → WRONG (too generic)
- Expected: "success" → WRONG (too generic, add details)

REQUIRED FORMAT - CONCRETE TEST CASES:
✅ Test name: "Collect temperature reading from sensor TEMP-001"
✅ Input: {{"instrument": "temperature_sensor", "sensor_id": "TEMP-001", "interval": "60_seconds"}}
✅ Expected: {{"value": 20.5, "unit": "celsius", "timestamp": "2025-11-17T12:30:00Z", "status": "valid"}}

COMPLETENESS REQUIREMENT:
- Create test cases for EVERY requirement (minimum 2 scenarios per requirement)
- If input has N requirements, output MUST have N test case groups
- Count requirements in input and ensure test case count matches exactly
- Include edge cases explicitly mentioned in source

EXTRACTION PROCESS:

Step 4: Create Test Cases
- Cover ALL variations mentioned in source (e.g., if source lists 6 instruments, test all 6)
- Use concrete, realistic data structures with actual values
- Include specific expected outputs with data types and formats
- Add edge cases explicitly mentioned in source:
  * Communication failures (satellite link loss, radio failure)
  * Hardware malfunctions (instrument failure, power issues)
  * Environmental conditions (high wind, extreme temperatures)
  * Failover scenarios (backup instrument switching, generator shutdown)

CONCRETE TEST CASE FORMAT - EXAMPLES:

❌ BAD - Generic Template (DO NOT USE):
  "Test: Verify that the system must collect weather data
   Expected: Functionality works as specified"
   
❌ BAD - Another Template (DO NOT USE):
  "Test: Verify that the system must [requirement]
   Expected: Functionality works as specified in the user story"

✅ GOOD - Specific with Concrete Data (USE THIS):
{{
  "test_name": "Collect temperature reading from sensor TEMP-001",
  "input": {{
    "instrument": "temperature_sensor",
    "sensor_id": "TEMP-001",
    "reading_interval": "60_seconds"
  }},
  "expected_output": {{
    "value": 20.5,
    "unit": "celsius",
    "timestamp": "2025-11-15T10:30:00Z",
    "status": "valid"
  }}
}}

✅ GOOD - Another Specific Example:
{{
  "test_name": "Transmit aggregated hourly data via satellite",
  "input": {{
    "data_type": "aggregated_weather_data",
    "satellite_status": "connected",
    "data_size": "1024_bytes",
    "timestamp": "2025-11-15T10:00:00Z"
  }},
  "expected_output": {{
    "transmission_status": "success",
    "bytes_sent": 1024,
    "acknowledgment_received": true,
    "transmission_time": "2025-11-15T10:00:05Z"
  }}
}}

TEST CASE FORMAT:
{{
  "testCases": [
    {{
      "requirement_id": 1,
      "scenarios": [
        {{
          "name": "Test [specific scenario with concrete data]",
          "input": {{
            "field": "concrete_value_with_type",
            "another_field": "concrete_value"
          }},
          "expected_output": {{
            "field": "concrete_value_with_type",
            "another_field": "concrete_value"
          }}
        }},
        {{
          "name": "Test [edge case scenario with concrete data]",
          "input": {{
            "field": "concrete_value"
          }},
          "expected_output": {{
            "field": "concrete_value_with_type"
          }}
        }}
      ]
    }}
  ]
}}

EDGE CASES TO COVER (if mentioned in source):
- Generator shutdown protocol in high wind (with concrete wind speed values from source)
- Backup instrument switching mechanism (with specific instrument IDs)
- Communication failure recovery process (with specific failure scenarios)
- Local data storage during outages (with specific storage capacity if mentioned)
- Data aggregation for bandwidth optimization (with specific data structures)

VALIDATION CHECKLIST BEFORE OUTPUT:
- [ ] Count requirements in input
- [ ] Count test case groups in output - MUST MATCH
- [ ] Each requirement has minimum 2 test scenarios
- [ ] Edge cases from source are included
- [ ] All test cases have concrete input/output data (not generic "verify that")
- [ ] No invented numbers or metrics in test cases

EXAMPLES OF WHAT NOT TO DO:
❌ Generic test outputs like "weather_data" instead of structured data
❌ Generic "Verify that the system must [requirement]" statements
❌ "Functionality works as specified" as expected output
❌ Inventing test scenarios not mentioned in source
❌ Missing test cases for some requirements
❌ Test cases without concrete input/output data

EXAMPLES OF WHAT TO DO:
✅ Specific test data: {{"temperature": 20.5, "pressure": 1013.2, "timestamp": "2025-11-15T10:30:00Z"}}
✅ Concrete input: {{"instrument": "temperature_sensor", "interval": "60s"}}
✅ Concrete expected output: {{"value": 20.5, "unit": "C", "status": "valid"}}
✅ Cover all edge cases mentioned in source (failures, environmental conditions, etc.)
✅ ONE test case group per requirement (if 5 requirements, then 5 test case groups)

Return ONLY valid JSON, no markdown, no explanations.
        """
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
    prompt = (PromptTemplate.from_template("""As a voter, you vote for the input that is more accurate, concise and easy
                                           to understand. Given two input texts, the first:\n
                                        {input_first}\n and the second:\n" {input_second}\n", which one you vote for?
                                           Please only answer with your vote."""))
    
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
        elif '2' in re_text.lower() or 'second' in re_text.lower():
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

def get_epics(deliverables: str, chat)->str:
    """Extract and refine epics from deliverables"""
    try:
        just_tasks = safe_json_loads(deliverables, {"Epics": []})
        _key = "Epics"
        new_key = "User Stories"
        _key_2 = "Deliverables"
        refine_tasks = {new_key: []}
        
        # Debug: Print what we got
        print(f"DEBUG get_epics: deliverables keys: {list(just_tasks.keys())}")
        print(f"DEBUG get_epics: Epics count: {len(just_tasks.get(_key, []))}")
        
        if _key not in just_tasks or not isinstance(just_tasks[_key], list):
            print(f"Warning: Invalid deliverables format, expected list under '{_key}'")
            print(f"DEBUG: just_tasks content: {just_tasks}")
            return json.dumps(refine_tasks, indent=4)
        
        for epic in just_tasks[_key]:
            try:
                epic_refined = refine_epics(epic, chat)
                new_devs = safe_json_loads(epic_refined, {})
                epic[_key_2] = new_devs
                refine_tasks[new_key].append(epic)
            except Exception as e:
                print(f"Error processing epic: {e}")
                # Continue with next epic
                continue
        
        epics = json.dumps(refine_tasks, indent=4)
        return epics
    except Exception as e:
        print(f"Error in get_epics: {e}")
        import traceback
        traceback.print_exc()
        # Return empty structure on error
        return json.dumps({"User Stories": []}, indent=4)
