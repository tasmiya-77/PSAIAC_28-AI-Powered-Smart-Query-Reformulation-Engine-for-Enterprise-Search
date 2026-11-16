import logging
from typing import List, Optional
import httpx

from app.core.config import settings
from app.services.reformulation.base import (
    BaseReformulationProvider,
    RateLimitError,
    AuthError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    MalformedResponseError,
    STABLE_SYSTEM_INSTRUCTION,
    build_user_prompt,
    parse_and_validate_candidates,
)

logger = logging.getLogger(__name__)


class GroqReformulationProvider(BaseReformulationProvider):
    """Groq API provider adapter for high-speed free-tier query reformulation."""

    name: str = "groq"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_MODEL
        self.base_url = (base_url or settings.GROQ_BASE_URL).rstrip("/")
        self.timeout = timeout if timeout is not None else settings.REFORMULATION_TIMEOUT_SECONDS

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def reformulate(
        self,
        query: str,
        intent: str,
        entities: List[str],
        context: Optional[str] = None,
    ) -> List[str]:
        if not self.is_configured():
            raise AuthError("Groq API key is not configured.")

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        user_content = build_user_prompt(query, intent, entities, context)
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": STABLE_SYSTEM_INSTRUCTION},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.3,
            "max_tokens": 512,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, json=payload)

            if response.status_code == 429:
                logger.warning("[GROQ] Rate limit reached (HTTP 429). Fast failover triggered.")
                raise RateLimitError("Groq rate limit exceeded (HTTP 429).")
            elif response.status_code in (401, 403):
                logger.warning(f"[GROQ] Authentication failure (HTTP {response.status_code}).")
                raise AuthError(f"Groq authentication error (HTTP {response.status_code}).")
            elif response.status_code >= 500:
                logger.warning(f"[GROQ] Server error (HTTP {response.status_code}).")
                raise ProviderUnavailableError(f"Groq server error (HTTP {response.status_code}).")
            elif response.status_code != 200:
                raise ProviderUnavailableError(f"Groq unexpected status HTTP {response.status_code}: {response.text}")

            data = response.json()
            raw_text = data["choices"][0]["message"]["content"]
            candidates = parse_and_validate_candidates(raw_text, query, entities)
            logger.info(f"[GROQ] Successfully generated {len(candidates)} candidates using model '{self.model}'.")
            return candidates

        except httpx.TimeoutException as exc:
            logger.warning(f"[GROQ] Request timed out after {self.timeout}s.")
            raise ProviderTimeoutError(f"Groq request timed out after {self.timeout}s.") from exc
        except (RateLimitError, AuthError, ProviderTimeoutError, ProviderUnavailableError, MalformedResponseError):
            raise
        except Exception as exc:
            logger.warning(f"[GROQ] Unexpected communication error: {str(exc)}")
            raise ProviderUnavailableError(f"Groq request failed: {str(exc)}") from exc
