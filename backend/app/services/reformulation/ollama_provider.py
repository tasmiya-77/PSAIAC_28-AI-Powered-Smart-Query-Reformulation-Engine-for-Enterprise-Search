import logging
from typing import List, Optional
import httpx

from app.core.config import settings
from app.services.reformulation.base import (
    BaseReformulationProvider,
    ProviderTimeoutError,
    ProviderUnavailableError,
    MalformedResponseError,
    STABLE_SYSTEM_INSTRUCTION,
    build_user_prompt,
    parse_and_validate_candidates,
)

logger = logging.getLogger(__name__)


class OllamaReformulationProvider(BaseReformulationProvider):
    """Local Ollama provider adapter running free local inference (qwen2.5:3b)."""

    name: str = "ollama"

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout if timeout is not None else settings.REFORMULATION_TIMEOUT_SECONDS

    def is_configured(self) -> bool:
        return bool(self.base_url and self.model)

    def reformulate(
        self,
        query: str,
        intent: str,
        entities: List[str],
        context: Optional[str] = None,
    ) -> List[str]:
        url = f"{self.base_url}/api/chat"
        user_content = build_user_prompt(query, intent, entities, context)

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": STABLE_SYSTEM_INSTRUCTION},
                {"role": "user", "content": user_content},
            ],
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.3,
            },
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload)

            if response.status_code == 404:
                # Fallback to /api/generate if /api/chat not found
                return self._fallback_generate(query, intent, entities, context)

            if response.status_code != 200:
                logger.warning(f"[OLLAMA] Server returned HTTP {response.status_code}: {response.text}")
                raise ProviderUnavailableError(f"Ollama returned HTTP {response.status_code}")

            data = response.json()
            raw_text = data.get("message", {}).get("content", "")
            candidates = parse_and_validate_candidates(raw_text, query, entities)
            logger.info(f"[OLLAMA] Generated {len(candidates)} candidates locally with model '{self.model}'.")
            return candidates

        except httpx.ConnectError as exc:
            logger.warning(f"[OLLAMA] Connection refused at {self.base_url}. Daemon may not be running.")
            raise ProviderUnavailableError(f"Could not connect to Ollama at {self.base_url}") from exc
        except httpx.TimeoutException as exc:
            logger.warning(f"[OLLAMA] Local inference timed out after {self.timeout}s.")
            raise ProviderTimeoutError(f"Ollama inference timed out after {self.timeout}s") from exc
        except (ProviderTimeoutError, ProviderUnavailableError, MalformedResponseError):
            raise
        except Exception as exc:
            logger.warning(f"[OLLAMA] Error during local query reformulation: {str(exc)}")
            raise ProviderUnavailableError(f"Ollama error: {str(exc)}") from exc

    def _fallback_generate(
        self,
        query: str,
        intent: str,
        entities: List[str],
        context: Optional[str] = None,
    ) -> List[str]:
        """Fallback to /api/generate endpoint for older Ollama versions."""
        url = f"{self.base_url}/api/generate"
        prompt = f"{STABLE_SYSTEM_INSTRUCTION}\n\n{build_user_prompt(query, intent, entities, context)}"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.3},
        }
        with httpx.Client(timeout=self.timeout) as client:
            res = client.post(url, json=payload)
        if res.status_code != 200:
            raise ProviderUnavailableError(f"Ollama /api/generate returned HTTP {res.status_code}")
        raw_text = res.json().get("response", "")
        return parse_and_validate_candidates(raw_text, query, entities)
