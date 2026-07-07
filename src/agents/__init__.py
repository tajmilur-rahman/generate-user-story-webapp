"""
Multi-Agent System for User Story Generation

This package contains specialized agents that work together to generate
high-quality user stories from requirement documents.

Agents:
- RequirementsAgent: Extracts and refines requirements
- EpicExtractorAgent: Groups requirements into epics (first pass)
- EpicRefinerAgent: Refines and merges epics (second pass)
- StoryAgent: Generates user stories with acceptance criteria
- TestCaseAgent: Generates test cases
- ReviewerAgent: Scores stories on INVEST criteria
- RewriterAgent: Improves low-quality stories
- StoryOrchestrator: Coordinates all agents and manages quality loops
"""

from .base_agent import BaseAgent
from .requirements_agent import RequirementsAgent
from .epic_extractor_agent import EpicExtractorAgent
from .epic_refiner_agent import EpicRefinerAgent
from .story_agent import StoryAgent
from .test_agent import TestCaseAgent
from .reviewer_agent import ReviewerAgent
from .rewriter_agent import RewriterAgent
from .orchestrator import StoryOrchestrator

__all__ = [
    'BaseAgent',
    'RequirementsAgent',
    'EpicExtractorAgent',
    'EpicRefinerAgent',
    'StoryAgent',
    'TestCaseAgent',
    'ReviewerAgent',
    'RewriterAgent',
    'StoryOrchestrator'
]
