import logging
from typing import List, Dict, Optional, Tuple

from app.core.config import settings
from app.services.reformulation.base import (
    BaseReformulationProvider,
    RateLimitError,
    AuthError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    MalformedResponseError,
)
from app.services.reformulation.groq_provider import GroqReformulationProvider
from app.services.reformulation.cloudflare_provider import CloudflareReformulationProvider
from app.services.reformulation.ollama_provider import OllamaReformulationProvider
from app.services.reformulation.gemini_provider import GeminiReformulationProvider
from app.services.reformulation.sambanova_provider import SambaNovaReformulationProvider

logger = logging.getLogger(__name__)


class MultiLLMReformulationService:
    """
    Dynamic Multi-LLM Query Reformulation Service (Free-Quota Only).
    Orchestrates provider execution, fast-failover on rate limits (429) or timeouts,
    local Ollama fallback, and sanitized logging.
    """

    def __init__(self):
        # Register available provider adapters
        self.providers: Dict[str, BaseReformulationProvider] = {
            "groq": GroqReformulationProvider(),
            "cloudflare": CloudflareReformulationProvider(),
            "gemini": GeminiReformulationProvider(),
            "ollama": OllamaReformulationProvider(),
            "sambanova": SambaNovaReformulationProvider(),
        }

    def get_configured_providers(self) -> List[Tuple[str, BaseReformulationProvider]]:
        """Parse REFORMULATION_PROVIDER_ORDER and return ordered list of active providers."""
        raw_order = settings.REFORMULATION_PROVIDER_ORDER or "groq,cloudflare,gemini,ollama"
        names = [name.strip().lower() for name in raw_order.split(",") if name.strip()]

        ordered = []
        for name in names:
            provider = self.providers.get(name)
            if provider:
                ordered.append((name, provider))
            else:
                logger.warning(f"[REFORMULATION] Unknown provider '{name}' in REFORMULATION_PROVIDER_ORDER.")
        return ordered

    def reformulate(
        self,
        query: str,
        intent: str,
        entities: List[str],
        context: Optional[str] = None,
    ) -> Tuple[Optional[List[str]], str]:
        """
        Execute query reformulation through the configured provider fallback chain.
        Follows FREE-QUOTA-ONLY policy:
          1. Tries configured hosted free-tier providers in order (Groq, Cloudflare, Gemini).
          2. On HTTP 429 (rate limit) or timeout, does NOT repeat retries; switches immediately.
          3. Falls back to local Ollama (qwen2.5:3b) when hosted providers fail or are unconfigured.
          4. Returns (candidates, provider_label). If all providers fail, returns (None, 'Algorithmic Fallback').
        """
        ordered_providers = self.get_configured_providers()
        attempted: List[str] = []

        for name, provider in ordered_providers:
            if not provider.is_configured():
                logger.debug(f"[REFORMULATION] Provider '{name}' is not configured (missing key/credentials). Skipping.")
                continue

            attempted.append(name)
            logger.info(f"[REFORMULATION] Attempting query reformulation via '{name}' provider...")

            try:
                candidates = provider.reformulate(
                    query=query,
                    intent=intent,
                    entities=entities,
                    context=context,
                )
                if candidates and len(candidates) >= 2:
                    provider_label = self._format_provider_label(name, provider)
                    logger.info(f"[REFORMULATION] Success with provider '{name}'. Candidate count: {len(candidates)}.")
                    return candidates, provider_label

            except RateLimitError as exc:
                # HTTP 429 / Quota exceeded: fast failover to next provider / local model
                logger.warning(
                    f"[REFORMULATION] {name.upper()} returned 429 (quota/rate limit exceeded). "
                    f"Fast failover immediately to next provider without retrying."
                )
                continue

            except AuthError as exc:
                logger.warning(f"[REFORMULATION] {name.upper()} authentication failed. Skipping provider.")
                continue

            except ProviderTimeoutError as exc:
                logger.warning(f"[REFORMULATION] {name.upper()} timed out. Switching to fallback provider.")
                continue

            except MalformedResponseError as exc:
                logger.warning(f"[REFORMULATION] {name.upper()} returned malformed or unparseable output: {str(exc)}.")
                continue

            except ProviderUnavailableError as exc:
                logger.warning(f"[REFORMULATION] {name.upper()} unavailable or server error: {str(exc)}.")
                continue

            except Exception as exc:
                logger.warning(f"[REFORMULATION] Unexpected failure calling {name.upper()}: {str(exc)}.")
                continue

        logger.info(
            f"[REFORMULATION] All configured LLM providers attempted ({', '.join(attempted) if attempted else 'none'}). "
            f"Switching to algorithmic fallback generator."
        )
        return None, "Algorithmic Fallback"

    def _format_provider_label(self, name: str, provider: BaseReformulationProvider) -> str:
        """Create a human-friendly provider label with active model identifier."""
        model_name = getattr(provider, "model", "")
        if name == "groq":
            return f"Groq ({model_name or settings.GROQ_MODEL})"
        elif name == "cloudflare":
            return f"Cloudflare Workers AI ({model_name or settings.CLOUDFLARE_MODEL})"
        elif name == "ollama":
            return f"Ollama Local ({model_name or settings.OLLAMA_MODEL})"
        elif name == "gemini":
            return f"Gemini ({model_name or settings.GEMINI_MODEL})"
        elif name == "sambanova":
            return f"SambaNova ({model_name or settings.SAMBANOVA_MODEL})"
        return name.capitalize()


# Singleton instance
multi_llm_reformulation_service = MultiLLMReformulationService()
