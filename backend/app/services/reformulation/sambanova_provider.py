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


class SambaNovaReformulationProvider(BaseReformulationProvider):
    """
    SambaNova provider adapter. Kept optional; on HTTP 429 it immediately triggers
    fast-failover to the next provider (e.g. local Ollama) without retries.
    """

    name: str = "sambanova"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.api_key = api_key or settings.SAMBANOVA_API_KEY
        self.model = model or settings.SAMBANOVA_MODEL
        self.base_url = (base_url or settings.SAMBANOVA_BASE_URL).rstrip("/")
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
            raise AuthError("SambaNova API key is not configured.")

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
                logger.warning("[SAMBANOVA] HTTP 429 rate limit encountered. Fast failover immediately without retrying.")
                raise RateLimitError("SambaNova rate limit reached (HTTP 429).")
            elif response.status_code in (401, 403):
                logger.warning(f"[SAMBANOVA] Authentication error HTTP {response.status_code}.")
                raise AuthError(f"SambaNova auth error HTTP {response.status_code}.")
            elif response.status_code >= 500:
                logger.warning(f"[SAMBANOVA] Server error HTTP {response.status_code}.")
                raise ProviderUnavailableError(f"SambaNova server error HTTP {response.status_code}.")
            elif response.status_code != 200:
                raise ProviderUnavailableError(f"SambaNova unexpected HTTP {response.status_code}: {response.text}")

            data = response.json()
            raw_text = data["choices"][0]["message"]["content"]
            candidates = parse_and_validate_candidates(raw_text, query, entities)
            logger.info(f"[SAMBANOVA] Generated {len(candidates)} candidate queries.")
            return candidates

        except httpx.TimeoutException as exc:
            logger.warning(f"[SAMBANOVA] Request timed out after {self.timeout}s.")
            raise ProviderTimeoutError(f"SambaNova request timed out after {self.timeout}s.") from exc
        except (RateLimitError, AuthError, ProviderTimeoutError, ProviderUnavailableError, MalformedResponseError):
            raise
        except Exception as exc:
            logger.warning(f"[SAMBANOVA] Request error: {str(exc)}")
            raise ProviderUnavailableError(f"SambaNova error: {str(exc)}") from exc
