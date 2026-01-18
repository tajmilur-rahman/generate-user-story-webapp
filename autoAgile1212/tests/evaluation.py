import os
import bert_score
from bert_score import score
from typing import Literal
import nltk
nltk.download('punkt')
from alignscore import AlignScore
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llm-test")

def evaluate(test: str, reference: str, eval_sys:Literal["BERTScore", "AlignScore"]):
    test = test.replace("\n", "").replace('\t', "").replace('\r', '').replace('  ', '')
    reference = reference.replace("\n", " ").replace('\t', '').replace('\r', '').replace('  ', '')
    logger.error(f"Test: {test}")
    logger.error(f"Reference: {reference}")
    if(eval_sys == "BERTScore"):
        P, R, F1 = score([test], [reference], lang='en', verbose=True)
        logger.info(f"System level Precision value: {P.mean():.3f}")
        logger.info(f"System level Recall score: {R.mean():.3f}")
        logger.info(f"System level F1 score: {F1.mean():.3f}")
        return F1
    elif(eval_sys=="AlignScore"):
        scorer = AlignScore(model='roberta-base', batch_size=32, device='cpu', ckpt_path='./AlignScore/AlignScore-base.ckpt', evaluation_mode='nli_sp')
        alignScore = scorer.score(contexts=[reference], claims=[test])
        logger.error(alignScore)
        return alignScore[0]
    else: 
        logger.error("Invalid evaluation system")
        raise ValueError("Invalid evaluation system")
