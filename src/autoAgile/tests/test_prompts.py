import logging
import unittest
import json
from utils.prompts import *

#from .test_doc_resources import *
from .insulim_resources import *
from .evaluation import evaluate

output_file = "insulim_output_gpt35.txt"
api_key = os.environ['auth_key']
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("utls-test")
trials = 10
Model = "gpt-3.5-turbo" 

def normalize(_min, _max, value):
    return (value - _min) / (_max - _min)

def check_text_similarity(text_left:str, text_right:str, model:str="gpt-3.5-turbo-instruct")->str:
    chat = ChatOpenAI(model=Model,temperature=0, openai_api_key=api_key)
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an ai to check whether the user input list of functional requirements
         have all the requirements specified in the expected requirements list. 
         Your reply should be in Json format with the reasoning process in key
         'reason' and the boolean result 'True' or 'False' with the key 'result'."""),
        ("ai", """This is the expected requirements list:{text_left}. Please input the list you have."""),
        ("human", "{text_right}")
    ])
    chain = prompt | chat | output_parser
    re = chain.invoke({"text_left": text_left, "text_right": text_right})
    return re

def geval(text_left:str, text_right:str, model:str="gpt-3.5-turbo-instruct")->float:
    chat = ChatOpenAI(model=Model, temperature=0, openai_api_key=api_key)
    prompt_text = """You will be given a news article. You will then be given one summary written for this article.
        Your task is to rate the summary on one metric.
        Please make sure you read and understand these instructions carefully. Please keep this document open while reviewing, and refer to it as needed.
        Evaluation Criteria:
        Consistency (1-5) - the factual alignment between the summary and the summarized source. A factually consistent summary contains only statements that are entailed by the source document. Annotators were also asked to penalize summaries that contained hallucinated facts. 
        Evaluation Steps:
        1. Read the news article carefully and identify the main facts and details it presents.
        2. Read the summary and compare it to the article. Check if the summary contains any factual errors that are not supported by the article.
        3. Assign a score for consistency based on the Evaluation Criteria.
        
        Source Text: 
        {Document}

        Summary: 
        {Summary}
        
        Evaluation Form (scores ONLY):
        Consistency:
        """
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_text),
    ])
    chain = prompt | chat | output_parser
    re = chain.invoke({"Document": text_left, "Summary": text_right})
    return float(re)

def test_extract_requirements():
    # Call the function
    align_scores = []
    bert_scores = []
    rat_type = "extract_requirements"
    max_align = evaluate(expected_requirements, expected_requirements, "AlignScore")
    min_align = evaluate("random string", expected_requirements, "AlignScore")
    max_bert = evaluate(expected_requirements, expected_requirements, "BERTScore")
    min_bert = evaluate("random string", expected_requirements, "BERTScore")
    for i in range(trials):
        chat = ChatOpenAI(model=Model, temperature=0, openai_api_key=api_key)
        result = rat(refine_doc, extract_functionarity, doc_text_raw, chat, "debug")
        # Assert the expected behavior based on the provided data
        assert type(result) is str
        logger.error(result)
        # Add more specific assertions based on the expected behavior of your function
        align = evaluate(result, expected_requirements, "AlignScore")       
        align_scores.append(normalize(min_align,max_align,align))
        score = evaluate(result, expected_requirements, "BERTScore")
        bert_scores.append(normalize(min_bert, max_bert,score))
    with open(output_file, "a") as f:
        f.write(f"{rat_type} align scores are: {align_scores}\n")
        f.write(f"{rat_type} bert scores are: {bert_scores}\n")


def test_extract_requirements_baseline():
    # Call the function
    rat_type = "extract_requirements"
    align_scores = []
    bert_scores = []
    max_align = evaluate(expected_requirements, expected_requirements, "AlignScore")
    min_align = evaluate("random string", expected_requirements, "AlignScore")
    max_bert = evaluate(expected_requirements, expected_requirements, "BERTScore")
    min_bert = evaluate("random string", expected_requirements, "BERTScore")
    for i in range(trials):
        chat = ChatOpenAI(model=Model, temperature=0, openai_api_key=api_key)
        result = extract_functionarity(doc_text_raw, chat, "debug")
        # Assert the expected behavior based on the provided data
        assert type(result) is str
        logger.error(result)
        # Add more specific assertions based on the expected behavior of your function
        align = evaluate(result, expected_requirements, "AlignScore")       
        align_scores.append(normalize(min_align,max_align,align))
        score = evaluate(result, expected_requirements, "BERTScore")
        bert_scores.append(normalize(min_bert, max_bert,score))
    with open(output_file, "a") as f:
        f.write(f"{rat_type} baseline align scores are: {align_scores}\n")
        f.write(f"{rat_type} baseline bert scores are: {bert_scores}\n")

def test_extract_epic():
    # Call the function
    rat_type = "extract_epics"
    align_scores = []
    bert_scores = []
    max_align = evaluate(expected_epics, expected_epics, "AlignScore")
    min_align = evaluate("random string", expected_epics, "AlignScore")
    max_bert = evaluate(expected_epics, expected_epics, "BERTScore")
    min_bert = evaluate("random string", expected_epics, "BERTScore")
    for i in range(trials):
        chat = ChatOpenAI(model=Model, temperature=0, openai_api_key=api_key)
        result = rat(refine_requirements, extract_epics, expected_requirements, chat, "prod")
        # Assert the expected behavior based on the provided data
        assert type(result) is str
        logger.error(result)
        # Add more specific assertions based on the expected behavior of your function
        align = evaluate(result, expected_epics, "AlignScore")       
        align_scores.append(normalize(min_align,max_align,align))
        score = evaluate(result, expected_epics, "BERTScore")
        bert_scores.append(normalize(min_bert, max_bert,score))
    with open(output_file, "a") as f:
        f.write(f"{rat_type} align scores are: {align_scores}\n")
        f.write(f"{rat_type} bert scores are: {bert_scores}\n")


def test_extract_epic_baseline():
    # Call the function
    rat_type = "extract_epics"
    align_scores = []
    bert_scores = []
    max_align = evaluate(expected_epics, expected_epics, "AlignScore")
    min_align = evaluate("random string", expected_epics, "AlignScore")
    max_bert = evaluate(expected_epics, expected_epics, "BERTScore")
    min_bert = evaluate("random string", expected_epics, "BERTScore")
    for i in range(trials):
        chat = ChatOpenAI(model=Model, temperature=0, openai_api_key=api_key)
        result = extract_epics(expected_requirements, chat, "prod")
        # Assert the expected behavior based on the provided data
        assert type(result) is str
        logger.error(result)
        # Add more specific assertions based on the expected behavior of your function
        align = evaluate(result, expected_epics, "AlignScore")       
        align_scores.append(normalize(min_align,max_align,align))
        score = evaluate(result, expected_epics, "BERTScore")
        bert_scores.append(normalize(min_bert, max_bert,score))
    with open(output_file, "a") as f:
        f.write(f"{rat_type} baseline align scores are: {align_scores}\n")
        f.write(f"{rat_type} baseline bert scores are: {bert_scores}\n")


def test_extract_testcase():
    # Call the function
    rat_type = "extract_testcases"
    align_scores = []
    bert_scores = []
    max_align = evaluate(expected_tests, expected_tests, "AlignScore")
    min_align = evaluate("random string", expected_tests, "AlignScore")
    max_bert = evaluate(expected_tests, expected_tests, "BERTScore")
    min_bert = evaluate("random string", expected_tests, "BERTScore")
    for i in range(trials):
        chat = ChatOpenAI(model=Model, temperature=0, openai_api_key=api_key)
        result = rat(refine_requirements, generate_test_cases, expected_requirements, chat, "prod")
        # Assert the expected behavior based on the provided data
        assert type(result) is str
        logger.error(result)
        # Add more specific assertions based on the expected behavior of your function
        align = evaluate(result, expected_tests, "AlignScore")       
        align_scores.append(normalize(min_align,max_align,align))
        score = evaluate(result, expected_tests, "BERTScore")
        bert_scores.append(normalize(min_bert, max_bert,score))
    with open(output_file, "a") as f:
        f.write(f"{rat_type} align scores are: {align_scores}\n")
        f.write(f"{rat_type} bert scores are: {bert_scores}\n")
    assert False


def test_extract_testcases_baseline():
    # Call the function
    rat_type = "extract_testcases"
    align_scores = []
    bert_scores = []
    max_align = evaluate(expected_tests, expected_tests, "AlignScore")
    min_align = evaluate("random string", expected_tests, "AlignScore")
    max_bert = evaluate(expected_tests, expected_tests, "BERTScore")
    min_bert = evaluate("random string", expected_tests, "BERTScore")
    for i in range(trials):
        chat = ChatOpenAI(model=Model, temperature=0, openai_api_key=api_key)
        result = generate_test_cases(expected_requirements, chat, "prod")
        # Assert the expected behavior based on the provided data
        assert type(result) is str
        logger.error(result)
        # Add more specific assertions based on the expected behavior of your function
        align = evaluate(result, expected_tests, "AlignScore")       
        align_scores.append(normalize(min_align,max_align,align))
        score = evaluate(result, expected_tests, "BERTScore")
        bert_scores.append(normalize(min_bert, max_bert,score))
    with open(output_file, "a") as f:
        f.write(f"{rat_type} baseline align scores are: {align_scores}\n")
        f.write(f"{rat_type} baseline bert scores are: {bert_scores}\n")
