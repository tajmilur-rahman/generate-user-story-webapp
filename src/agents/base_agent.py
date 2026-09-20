from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from langchain_ollama import ChatOllama
import os
import json
import logging

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all agents - handles common LLM interaction"""

    def __init__(
        self,
        name: str,
        role: str,
        goal: str,
        temperature: float = 0.0
    ):
        self.name = name
        self.role = role
        self.goal = goal

        # Use same model as current system
        model_name = os.getenv('OLLAMA_MODEL', 'qwen3-coder:30b')

        llm = ChatOllama(
            model=model_name,
            temperature=temperature,
            base_url="http://localhost:11434",
            format="json"  # Enforce JSON output
        )

        # Retry transient Ollama failures with exponential backoff AND jitter.
        #
        # Jitter is the part that matters here: the orchestrator runs 5 workers
        # against a single Ollama instance, so failures tend to arrive together.
        # Without jitter those workers would back off in lockstep and re-collide
        # on every attempt (the thundering-herd problem). LangChain's with_retry
        # is tenacity-backed and enables jitter by default.
        self.max_attempts = int(os.getenv('OLLAMA_MAX_ATTEMPTS', '3'))
        self.llm = llm.with_retry(stop_after_attempt=self.max_attempts)

        logger.info(
            f"[{name}] Initialized with model: {model_name} "
            f"(max_attempts={self.max_attempts})"
        )

    @abstractmethod
    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        """Build specialized prompt for this agent's role"""
        pass

    def run(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent task"""
        try:
            logger.info(f"[{self.name}] Starting task...")

            # Build specialized prompt
            system_prompt = self.get_system_prompt(context)
            full_prompt = f"{system_prompt}\n\n{task}"

            # Call LLM
            response = self.llm.invoke(full_prompt)

            # Extract content from response
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)

            # Parse JSON response
            result = self._extract_json(response_text)

            logger.info(f"[{self.name}] Completed successfully")

            return {
                "agent": self.name,
                "success": True,
                "output": result
            }

        except Exception as e:
            # Reached only after with_retry has exhausted every attempt.
            logger.error(
                f"[{self.name}] Failed after {self.max_attempts} attempts: {e}"
            )
            return {
                "agent": self.name,
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "attempts": self.max_attempts
            }

    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from response - reuse _strip_fences logic"""
        text = text.strip()

        # Remove markdown fences
        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        # Find JSON boundaries
        start = text.find('{')
        end = text.rfind('}') + 1

        if start == -1 or end == 0:
            raise ValueError(f"No JSON found in response: {text[:200]}")

        json_text = text[start:end]
        return json.loads(json_text)
