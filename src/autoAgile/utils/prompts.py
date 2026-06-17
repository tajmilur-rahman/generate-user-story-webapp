import os
import unicodedata
import json
from docx import Document
# Updated imports for modern LangChain (all moved to langchain_core)
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
# Note: ChatOpenAI import kept for backward compatibility, but llm_factory should be used
try:
    from langchain_openai import ChatOpenAI, OpenAI
except ImportError:
    pass

#set env variable auth_key to be the key
output_parser = StrOutputParser()
threshold = 5

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
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an software engineer to develop the functional requirements from the given software product
         design document. Integration testing is always one of the requirements. Your response should only have the list of the functional requirements."""),
        ("user", "{input}")
    ])
    chain = prompt | chat | output_parser
    re = chain.invoke({"input": doc_text})
    return re

def compare_answer(answer_left, answer_right,chat)->bool:
    prompt = (PromptTemplate.from_template("""Please compare the two input software requirement lists and determine whether
                                           they are describing the same list of requirements. Given the first list:\n
                                        {input_first}\n and the second:\n" {input_second}\n", are they describing the
                                           same requirements? Please provide reasoning steps in your answer, also with
                                           keyword yes indicating they are the same or no indicating they are not the
                                           same."""))

    # Use LangChain's LCEL (modern syntax)
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
    prompt = (PromptTemplate.from_template("""As a software developer, you vote for the software requirement list that is more detailed and specific.\n
                                           \nGiven two input texts, the first:\n
                                        {input_first}\n and the second:\n" {input_second}\n", which one you vote for?
                                           Please only answer with your vote."""))

    # Use LangChain's LCEL (modern syntax)
    chain = prompt | chat | output_parser
    re_text = chain.invoke({"input_first":answer_left, "input_second":answer_right})
    
    better = None
    if '1' in re_text.lower() or 'first' in re_text.lower():
        better = answer_left
    elif '2' in re_text.lower() or "second" in re_text.lower():
        better = answer_right
    else:
        # Default to first answer if unclear
        better = answer_left
        
    if mode == "debug":
        print("=============================\n")
        print(re_text)
        print("===========the better result is=========\n")
        print(better)
        print("=============================\n")
    return better

def c_o_t(answers: list[str], chat, mode="debug")->str:
    better = answers[0]
    for answer in answers[1:]:
        better = rank_answer(better, answer, chat, mode)
    return better


def extract_functionarity(doc_text:str,chat, mode="debug")->str:
    requirements = [extract_list(doc_text, chat) for i in range(threshold)]
    return c_o_t(requirements, chat, mode)

def refine_requirements(requirements:str,chat,mode)->str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are the project manager who will refine the given functional requirements to combine redundant
         requirements and add missing requirements according to the existed one.
         Your response should only have the list of the refined functional requirements."""),
        ("user", "{input}")
    ])
    chain = prompt | chat | output_parser
    re = chain.invoke({"input": requirements})
    return re

def extract_epics(requirements:str,chat, mode)->str:
    pp = """given the input software requirements,please give us the deliverables that we can assign to our
         developers. Each requirement should has its own description. For each functional requirement, the deliverables should be selected from architecture design, database
         schema design, unit tests, user training documentation and production support plan based on your judgement.
         Your response should be in Json format. This this an example output:
         '{{
            "Epics": [
                {{
                    "User Story": "The system must perform local data processing and aggregation before transmitting data via satellite.",
                    "Deliverables": {{
                        "architecture_design": "Design of the data processing and aggregation modules within the system."
                    }}
                }}
            ]
          }}'.
        """
    prompt = ChatPromptTemplate.from_messages([
        ("system", pp),
        ("user", "{input}")
    ])
    chain = prompt | chat | output_parser
    re = chain.invoke({"input": requirements})
    return re.replace("json","").replace("```","")

def extract_epics_v2(requirements:str,chat, mode)->str:
    """Enhanced v2: Same structure as v1, but with better prompts for higher quality output"""
    pp = """Given the input software requirements, create comprehensive, detailed user stories with specific deliverables.

IMPORTANT: You must create user stories that are:
1. DETAILED and SPECIFIC - Reference exact components, features, and functionality from the requirements
2. COMPREHENSIVE - Combine multiple related requirements into cohesive user stories where appropriate
3. ACTIONABLE - Deliverables should be clear enough for developers to implement

USER STORY FORMAT:
- Write clear, complete descriptions of what the system must do
- Include WHO benefits (users, system, administrators), WHAT they need, and WHY it matters
- Be specific about the functionality, not generic
- Reference specific system components, modules, or features mentioned in requirements

DELIVERABLE DESCRIPTIONS MUST BE HIGHLY SPECIFIC:
- Don't just say "Design of the module" - specify WHICH modules, WHAT components, WHAT functionality
- Don't just say "Tests to ensure accuracy" - specify WHAT is being tested, WHAT accuracy means for this feature
- Include technical details: algorithms, data structures, interfaces, workflows
- Reference specific components from the user story

DELIVERABLE OPTIONS (select 2-4 per user story based on requirements):
- architecture_design: Design of specific modules, components, algorithms, or system architecture
- database_schema_design: Database schema, data models, or data storage design
- unit_tests: Tests to verify specific functionality and accuracy
- user_training_documentation: Documentation for end users
- production_support_plan: Plans for system availability, monitoring, maintenance, or operations

Your response must be in JSON format following this exact structure:
{{
    "Epics": [
        {{
            "User Story": "The [specific system/component] must [detailed action with specific components] using [specific technology/approach], so that [specific benefit with measurable outcome].",
            "Deliverables": {{
                "architecture_design": "Design of the [specific module names] including [specific components: data flow, algorithms, interfaces] to enable [specific functionality].",
                "database_schema_design": "Schema for storing and retrieving [specific data types] including [specific fields/tables] to support [specific queries/operations].",
                "unit_tests": "Tests to ensure [specific component] correctly [specific behavior] with [specific test scenarios: edge cases, error conditions]."
            }}
        }},
        {{
            "User Story": "The system must include integration testing to verify that all components work together as intended and meet the specified requirements.",
            "Deliverables": {{
                "unit_tests": "Comprehensive integration tests to validate the interaction between [list specific components], verify end-to-end functionality, and ensure seamless operation of the complete system."
            }}
        }}
    ]
}}

CRITICAL REQUIREMENTS:
1. Each user story should be 40-100 words (not too short!)
2. Deliverable descriptions should be 20-50 words each (highly detailed!)
3. Always include "Integration Testing" as the final user story
4. Reference specific components, modules, features from the requirements document
5. Be precise about what needs to be designed, built, or tested
6. Combine related requirements into single cohesive user stories where it makes sense

BAD EXAMPLE (too vague):
{{
    "User Story": "The system must process data.",
    "Deliverables": {{
        "architecture_design": "Design of the processing module."
    }}
}}

GOOD EXAMPLE (specific and detailed):
{{
    "User Story": "The insulin pump system must continuously monitor the user's blood sugar levels using an implanted microsensor and accurately calculate the blood sugar level from the electrical conductivity data provided by the sensor, so that insulin delivery can be precisely controlled.",
    "Deliverables": {{
        "architecture_design": "Design of the continuous monitoring and data calculation modules within the insulin pump system, including sensor interface specifications and blood sugar calculation algorithms.",
        "database_schema_design": "Schema for storing and retrieving blood sugar data readings, calculation results, and historical trends to support real-time monitoring and analysis.",
        "unit_tests": "Tests to ensure the microsensor's data collection occurs continuously without interruption and blood sugar calculation accuracy is within required medical standards."
    }}
}}
"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", pp),
        ("user", "{input}")
    ])
    chain = prompt | chat | output_parser
    re = chain.invoke({"input": requirements})
    return re.replace("json","").replace("```","")

def refine_epics(epic:str,chat)->str:
    pp = """given the input epic and its deliverables, please generate definition of done for each deliverable.
         Your response should be in Json format."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", pp),
        ("user", "{input}")
    ])
    chain = prompt | chat | output_parser
    re = chain.invoke({"input": epic})
    return re.replace("json","").replace("```","")

def refine_epics_v2(epic:str,chat)->str:
    """Enhanced v2: Same structure as v1, but generates detailed Definition of Done arrays"""
    pp = """Given the input epic with User Story and Deliverables, generate a comprehensive, detailed Definition of Done for each deliverable.

For each deliverable, create 5-7 specific, actionable, and measurable Definition of Done criteria that:
1. Clearly define what "complete" means for that deliverable
2. Include technical specifications and implementation details
3. Reference specific components, modules, or functionality from the user story
4. Are verifiable and testable (someone can check if it's done)
5. Include quality criteria (code coverage, performance, accuracy standards)
6. Include review/approval requirements where appropriate
7. Are SPECIFIC to this user story (not generic)

Your response must be in JSON format, expanding the input structure with detailed DoD arrays.

EXAMPLE INPUT:
{{
    "User Story": "The insulin pump system must continuously monitor the user's blood sugar levels using an implanted microsensor and accurately calculate the blood sugar level from the data provided.",
    "Deliverables": {{
        "architecture_design": "Design of the continuous monitoring and data calculation modules within the insulin pump system.",
        "unit_tests": "Tests to ensure the microsensor's data collection and blood sugar calculation accuracy."
    }}
}}

EXAMPLE OUTPUT:
{{
    "User Story": "The insulin pump system must continuously monitor the user's blood sugar levels using an implanted microsensor and accurately calculate the blood sugar level from the data provided.",
    "Deliverables": {{
        "architecture_design": {{
            "description": "Design of the continuous monitoring and data calculation modules within the insulin pump system.",
            "definition_of_done": [
                "Complete system architecture diagram showing monitoring module, data calculation module, and sensor interface with all component interactions",
                "Detailed design document for blood sugar monitoring module including sensor data acquisition specifications and sampling frequency",
                "Detailed design document for blood sugar calculation module including algorithms for converting electrical conductivity to glucose levels",
                "Data flow diagrams showing how sensor readings move through the system to calculation output",
                "API specifications for all module interfaces including data formats and error codes",
                "Error handling and failover mechanisms documented for sensor disconnection and data corruption scenarios",
                "Design reviewed and approved by technical lead and medical safety officer"
            ]
        }},
        "unit_tests": {{
            "description": "Tests to ensure the microsensor's data collection and blood sugar calculation accuracy.",
            "definition_of_done": [
                "Unit tests written for all monitoring functions achieving minimum 90% code coverage",
                "Tests verify sensor data reading occurs continuously without gaps or interruptions",
                "Tests validate correct blood sugar calculation from sensor electrical conductivity readings",
                "Tests confirm calculation accuracy within required medical standards (±5% margin)",
                "Edge case tests for sensor malfunction, data corruption, and communication failures",
                "All tests passing in CI/CD pipeline with zero failures",
                "Test documentation completed with test case descriptions, inputs, and expected results"
            ]
        }}
    }}
}}

CRITICAL REQUIREMENTS:
- PRESERVE the User Story text exactly as provided in input
- Each deliverable must have 5-7 specific Definition of Done items (not more, not less)
- DoD items must be 15-30 words each (detailed enough to be actionable)
- Reference specific technical details from the user story
- Be concrete and specific (avoid generic phrases like "ensure quality" or "test thoroughly")
- Include measurable criteria where possible (percentages, counts, standards)
- Each DoD item should start with a clear action or deliverable

BAD EXAMPLE (too generic):
{{
    "definition_of_done": [
        "Design is complete",
        "Tests pass",
        "Documentation exists"
    ]
}}

GOOD EXAMPLE (specific and detailed):
{{
    "definition_of_done": [
        "Complete architecture diagram showing all 5 modules (sensor interface, data processor, calculator, storage, alert system) with detailed component interactions",
        "Unit tests written for all 12 calculation functions achieving 92% code coverage measured by coverage.py",
        "Test documentation completed including 25 test cases with specific inputs, expected outputs, and edge case scenarios"
    ]
}}

Your response should preserve the User Story exactly as provided, and expand each deliverable with a detailed definition_of_done array.
"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", pp),
        ("user", "{input}")
    ])
    chain = prompt | chat | output_parser
    re = chain.invoke({"input": epic})
    return re.replace("json","").replace("```","")

def generate_test_cases(requirements:str,chat, mode)->str:
    pp = """given the input software requirements,please generate test cases for each requirement that we can use to
    verify the completeness of those requirements.
         Your response should be in Json format."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", pp),
        ("user", "{input}")
    ])
    chain = prompt | chat | output_parser
    re = chain.invoke({"input": requirements})
    return re.replace("json","").replace("```","")

def generate_test_cases_v2(requirements:str,chat, mode)->str:
    """Enhanced v2: Same structure as v1, but generates highly detailed test cases"""
    pp = """Given the input software requirements, generate comprehensive, detailed test cases for each requirement that can actually be executed by QA testers.

Each test case MUST include:
1. id: Unique sequential identifier (format: "TC1", "TC2", "TC3", etc.)
2. description: Clear, specific description of what functionality is being tested (15-30 words)
3. steps: Array of 3-5 detailed, actionable step-by-step procedures that a tester can follow
4. expected_result: Specific, measurable expected outcome that can be verified (not generic like "works correctly")

Your response must be in JSON format following this exact structure:
{{
  "test_cases": [
    {{
      "requirement": "Copy the exact requirement text being tested here",
      "test_cases": [
        {{
          "id": "TC1",
          "description": "Verify that [specific component] [specific action] under [specific conditions]",
          "steps": [
            "Specific action step with actual values or parameters",
            "Another actionable step with expected intermediate result",
            "Measurement or verification step with specific criteria"
          ],
          "expected_result": "Specific measurable outcome with actual values, thresholds, or success criteria"
        }},
        {{
          "id": "TC2",
          "description": "Check [specific functionality] accuracy against [known standard or baseline]",
          "steps": [
            "Setup step with specific configuration details",
            "Execute test with specific test data",
            "Compare results with specific comparison method"
          ],
          "expected_result": "Results match expected values within [specific margin or tolerance]"
        }}
      ]
    }}
  ]
}}

CRITICAL REQUIREMENTS:
- Each requirement should have 2-3 test cases covering different aspects (normal operation, edge cases, error conditions)
- Test IDs must be strictly sequential: TC1, TC2, TC3... (no gaps, no duplicates)
- Steps must be 10-25 words each (specific enough to execute, not too verbose)
- Expected results must be 15-30 words (specific enough to verify pass/fail)
- Reference actual system components, values, thresholds from the requirements
- Include concrete test data, parameters, or configurations
- Cover positive scenarios, negative scenarios, and edge cases
- NO generic phrases like "system works", "data is correct", "test passes"

GOOD EXAMPLE (specific and executable):
{{
  "requirement": "The insulin pump system must continuously monitor the user's blood sugar levels using an implanted microsensor.",
  "test_cases": [
    {{
      "id": "TC1",
      "description": "Verify that the microsensor continuously monitors blood sugar levels without interruption for 24 hours",
      "steps": [
        "Ensure the microsensor is properly implanted, calibrated, and connected to the monitoring system",
        "Start the monitoring process and record the start timestamp",
        "Monitor and log data output continuously for 24 hours without system intervention",
        "Review the complete data log for any gaps, missing readings, or interruptions"
      ],
      "expected_result": "Continuous data output captured every 5 minutes for full 24-hour period with zero gaps or missing data points"
    }},
    {{
      "id": "TC2",
      "description": "Check the accuracy of blood sugar level readings against a medically approved glucose meter at various glucose concentrations",
      "steps": [
        "Collect simultaneous blood sugar readings from both the microsensor and a calibrated medical glucose meter",
        "Test at five different glucose levels: 70, 100, 150, 200, and 250 mg/dL",
        "Compare the microsensor readings against the glucose meter readings for each test point",
        "Calculate the percentage difference between sensor and meter readings"
      ],
      "expected_result": "Microsensor readings match the glucose meter readings within ±5% margin of error across all tested glucose concentrations"
    }}
  ]
}}

BAD EXAMPLE (too generic - DO NOT DO THIS):
{{
  "requirement": "System monitors data",
  "test_cases": [
    {{
      "id": "1",
      "description": "Test monitoring",
      "steps": [
        "Start system",
        "Check if it works"
      ],
      "expected_result": "System works correctly"
    }}
  ]
}}

Remember: Test cases must be SPECIFIC enough that a QA tester can execute them without asking clarifying questions. Include actual values, thresholds, durations, and success criteria.
"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", pp),
        ("user", "{input}")
    ])
    chain = prompt | chat | output_parser
    re = chain.invoke({"input": requirements})
    return re.replace("json","").replace("```","")

def rat(refine, thought, x,chat, mode="prod"):
    prompt = (PromptTemplate.from_template("""As a voter, you vote for the input that is more accurate, concise and easy
                                           to understand. Given two input texts, the first:\n
                                        {input_first}\n and the second:\n" {input_second}\n", which one you vote for?
                                           Please only answer with your vote."""))

    x1 = refine(x, chat,mode)
    if mode == "debug":
        print("Refine successfully:\n")
        print("=============================\n")
        print(x1)
        print("=============================\n")
    
    # Use LangChain's LCEL (modern syntax)
    chain = prompt | chat | output_parser
    re_text = chain.invoke({"input_first":x, "input_second":x1})
    
    if mode == "debug":
        print(re_text)
    
    better = None
    if '1' in re_text.lower() or 'first' in re_text.lower():
        better = x
    elif '2' in re_text.lower() or 'second' in re_text.lower():
        better = x1
    else:
        # Default to refined version if unclear
        better = x1
    
    x2 = thought(better, chat, mode)
    return x2

def get_epics(deliverables: str, chat)->str:
    just_tasks = json.loads(deliverables)
    _key = "Epics"
    new_key = "User Stories"
    _key_2="Deliverables"
    refine_tasks = {new_key:[]}
    for epic in just_tasks[_key]:
        new_devs = json.loads(refine_epics(epic, chat))
        epic[_key_2] = new_devs
        refine_tasks[new_key].append(epic)
    epics = json.dumps(refine_tasks, indent=4)
    return epics

def get_epics_v2(deliverables: str, chat)->str:
    """Improved version using refine_epics_v2 for detailed Definition of Done"""
    just_tasks = json.loads(deliverables)
    _key = "Epics"
    new_key = "User Stories"
    _key_2="Deliverables"
    refine_tasks = {new_key:[]}
    for epic in just_tasks[_key]:
        new_devs = json.loads(refine_epics_v2(epic, chat))
        epic[_key_2] = new_devs
        refine_tasks[new_key].append(epic)
    epics = json.dumps(refine_tasks, indent=4)
    return epics
