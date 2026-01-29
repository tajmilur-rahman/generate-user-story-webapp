import os
import unicodedata
import json
from docx import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

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

    # Use LangChain's LCEL (LangChain Expression Language)
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

def rank_answer(answer_left, answer_right,chat, mode="debug")->bool:
    prompt = (PromptTemplate.from_template("""As a software developer, you vote for the software requirement list that is more detailed and specific.\n
                                           \nGiven two input texts, the first:\n
                                        {input_first}\n and the second:\n" {input_second}\n", which one you vote for?
                                           Please only answer with your vote."""))
        
    # Use LangChain's LCEL (LangChain Expression Language)
    chain = prompt | chat | output_parser
    re_text = chain.invoke({"input_first":answer_left, "input_second":answer_right})
    
    better = None
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
    
    # Use LangChain's LCEL (LangChain Expression Language)
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
