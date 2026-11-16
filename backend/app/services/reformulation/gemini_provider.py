import logging
from typing import List, Optional

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


class GeminiReformulationProvider(BaseReformulationProvider):
    """Google Gemini provider adapter preserving existing Gemini 2.5 Flash integration."""

    name: str = "gemini"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL

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
            raise AuthError("Gemini API key is not configured.")

        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)

            full_prompt = (
                f"{STABLE_SYSTEM_INSTRUCTION}\n\n"
                f"{build_user_prompt(query, intent, entities, context)}"
            )

            response = client.models.generate_content(
                model=self.model,
                contents=full_prompt,
            )

            if not response or not response.text:
                raise MalformedResponseError("Gemini returned empty response.")

            candidates = parse_and_validate_candidates(response.text, query, entities)
            logger.info(f"[GEMINI] Generated {len(candidates)} candidate queries using model '{self.model}'.")
            return candidates

        except Exception as exc:
            err_str = str(exc)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                logger.warning("[GEMINI] Gemini rate limit / quota exceeded (429 RESOURCE_EXHAUSTED).")
                raise RateLimitError(f"Gemini rate limit exceeded: {err_str}") from exc
            elif "401" in err_str or "403" in err_str or "API_KEY_INVALID" in err_str:
                logger.warning("[GEMINI] Gemini API key invalid.")
                raise AuthError(f"Gemini authentication failed: {err_str}") from exc
            elif "timed out" in err_str.lower() or "timeout" in err_str.lower():
                logger.warning("[GEMINI] Gemini request timed out.")
                raise ProviderTimeoutError(f"Gemini request timed out: {err_str}") from exc
            elif isinstance(exc, (RateLimitError, AuthError, ProviderTimeoutError, MalformedResponseError)):
                raise
            else:
                logger.warning(f"[GEMINI] Gemini API error: {err_str}")
                raise ProviderUnavailableError(f"Gemini call failed: {err_str}") from exc
