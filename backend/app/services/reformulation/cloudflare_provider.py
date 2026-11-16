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


class CloudflareReformulationProvider(BaseReformulationProvider):
    """Cloudflare Workers AI REST API provider adapter for free allowance reformulation."""

    name: str = "cloudflare"

    def __init__(
        self,
        account_id: Optional[str] = None,
        api_token: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.account_id = account_id or settings.CLOUDFLARE_ACCOUNT_ID
        self.api_token = api_token or settings.CLOUDFLARE_API_TOKEN
        self.model = model or settings.CLOUDFLARE_MODEL
        self.timeout = timeout if timeout is not None else settings.REFORMULATION_TIMEOUT_SECONDS

    def is_configured(self) -> bool:
        return bool(
            self.account_id and self.account_id.strip() and
            self.api_token and self.api_token.strip()
        )

    def reformulate(
        self,
        query: str,
        intent: str,
        entities: List[str],
        context: Optional[str] = None,
    ) -> List[str]:
        if not self.is_configured():
            raise AuthError("Cloudflare Workers AI account ID or API token is not configured.")

        url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/{self.model}"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

        user_content = build_user_prompt(query, intent, entities, context)
        payload = {
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
                logger.warning("[CLOUDFLARE] Rate limit reached (HTTP 429). Fast failover triggered.")
                raise RateLimitError("Cloudflare rate limit exceeded (HTTP 429).")
            elif response.status_code in (401, 403):
                logger.warning(f"[CLOUDFLARE] Authentication error (HTTP {response.status_code}).")
                raise AuthError(f"Cloudflare authentication error (HTTP {response.status_code}).")
            elif response.status_code >= 500:
                logger.warning(f"[CLOUDFLARE] Server error (HTTP {response.status_code}).")
                raise ProviderUnavailableError(f"Cloudflare server error (HTTP {response.status_code}).")
            elif response.status_code != 200:
                raise ProviderUnavailableError(f"Cloudflare unexpected status HTTP {response.status_code}: {response.text}")

            data = response.json()
            if not data.get("success", False) and "errors" in data and data["errors"]:
                err_msg = "; ".join(e.get("message", "Unknown error") for e in data["errors"])
                logger.warning(f"[CLOUDFLARE] Cloudflare API error: {err_msg}")
                raise ProviderUnavailableError(f"Cloudflare API returned error: {err_msg}")

            result = data.get("result", {})
            if isinstance(result, dict):
                raw_text = result.get("response", "")
            elif isinstance(result, str):
                raw_text = result
            else:
                raw_text = str(result)

            candidates = parse_and_validate_candidates(raw_text, query, entities)
            logger.info(f"[CLOUDFLARE] Generated {len(candidates)} candidates using model '{self.model}'.")
            return candidates

        except httpx.TimeoutException as exc:
            logger.warning(f"[CLOUDFLARE] Request timed out after {self.timeout}s.")
            raise ProviderTimeoutError(f"Cloudflare request timed out after {self.timeout}s.") from exc
        except (RateLimitError, AuthError, ProviderTimeoutError, ProviderUnavailableError, MalformedResponseError):
            raise
        except Exception as exc:
            logger.warning(f"[CLOUDFLARE] Unexpected error: {str(exc)}")
            raise ProviderUnavailableError(f"Cloudflare request failed: {str(exc)}") from exc
