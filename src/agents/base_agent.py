from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type

from pydantic import BaseModel, ValidationError
from langchain_ollama import ChatOllama
from langchain_core.runnables import RunnableLambda
import httpx
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
        temperature: float = 0.0,
        output_model: Optional[Type[BaseModel]] = None
    ):
        self.name = name
        self.role = role
        self.goal = goal
        # Output contract. When set, run() validates the parsed JSON against it
        # so a malformed response fails here, naming the bad field, instead of
        # surfacing as a KeyError several layers downstream.
        self.output_model = output_model

        # Use same model as current system
        model_name = os.getenv('OLLAMA_MODEL', 'qwen3-coder:30b')

        # A stalled call is worse than a failed one: it blocks a worker thread
        # forever, never raises, and so can never be retried. ChatOllama exposes
        # no `timeout` field, but client_kwargs is forwarded to the underlying
        # httpx client, which bounds the request at the transport layer.
        #
        # Budgets are env-tunable because a 7B model on a laptop GPU and a 30B
        # model on a workstation need very different allowances.
        timeout_s = float(os.getenv('OLLAMA_TIMEOUT', '180'))
        connect_timeout_s = float(os.getenv('OLLAMA_CONNECT_TIMEOUT', '10'))
        num_predict = int(os.getenv('OLLAMA_NUM_PREDICT', '4096'))
        base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')

        llm = ChatOllama(
            model=model_name,
            temperature=temperature,
            base_url=base_url,
            format="json",  # Enforce JSON output
            # Cap generation length. An unbounded response is the other way a
            # call runs away, and it is the cheaper one to prevent.
            num_predict=num_predict,
            client_kwargs={
                "timeout": httpx.Timeout(timeout_s, connect=connect_timeout_s)
            }
        )

        # Compose parse+validate INTO the retried unit rather than running it
        # after invoke() returns. A schema violation is usually transient -- the
        # same prompt often succeeds on the next attempt -- so it should be
        # retried like any other failure. Retrying only the network call would
        # leave the most common failure mode unretried.
        #
        # Jitter matters here: the orchestrator runs 5 workers against a single
        # Ollama instance, so failures tend to arrive together. Without jitter
        # those workers back off in lockstep and re-collide on every attempt
        # (the thundering-herd problem). LangChain's with_retry is
        # tenacity-backed and enables jitter by default.
        self.max_attempts = int(os.getenv('OLLAMA_MAX_ATTEMPTS', '3'))
        self.llm = llm
        self._chain = (
            llm | RunnableLambda(self._coerce_output)
        ).with_retry(stop_after_attempt=self.max_attempts)

        logger.info(
            f"[{name}] Initialized with model: {model_name} "
            f"(timeout={timeout_s}s, max_attempts={self.max_attempts})"
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

            # Call LLM. Parsing and contract validation happen inside the
            # chain, so both are covered by the retry policy.
            result = self._chain.invoke(full_prompt)

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

    def _coerce_output(self, response: Any) -> Dict[str, Any]:
        """
        Turn a raw LLM response into a validated dict.

        Runs inside the retried chain, so a parse failure or a contract
        violation is retried rather than returned as a hard failure.

        Args:
            response: Raw LLM response

        Returns:
            Parsed, contract-validated output

        Raises:
            ValueError: No JSON found, or output violates the declared contract
        """
        response_text = getattr(response, 'content', None) or str(response)

        result = self._extract_json(response_text)

        if self.output_model is None:
            return result

        try:
            validated = self.output_model.model_validate(result)
        except ValidationError as ve:
            # Name the offending fields. The previous behaviour surfaced this
            # as a KeyError several layers downstream, where the message said
            # nothing about which agent produced the bad output.
            fields = "; ".join(
                f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}"
                for err in ve.errors()[:5]
            )
            raise ValueError(
                f"{self.name} returned output violating its contract ({fields})"
            ) from ve

        return validated.model_dump()

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
