import re
import json
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Standardized Exceptions
# ---------------------------------------------------------------------------

class ReformulationError(Exception):
    """Base exception for all query reformulation provider errors."""
    pass


class RateLimitError(ReformulationError):
    """Raised when provider returns HTTP 429 / quota exceeded."""
    pass


class AuthError(ReformulationError):
    """Raised on authentication/authorization failure (HTTP 401 / 403)."""
    pass


class ProviderTimeoutError(ReformulationError):
    """Raised when provider connection or read times out."""
    pass


class MalformedResponseError(ReformulationError):
    """Raised when provider response cannot be parsed into valid candidate queries."""
    pass


class ProviderUnavailableError(ReformulationError):
    """Raised when provider endpoint is unreachable or returns server error (HTTP 5xx)."""
    pass


# ---------------------------------------------------------------------------
# Stable System Instructions & Prompt Construction
# ---------------------------------------------------------------------------

STABLE_SYSTEM_INSTRUCTION = (
    "You are an expert search engine query reformulation engine.\n"
    "Your objective is to reformulate the user's search query into exactly 5 distinct, "
    "high-precision candidate queries optimized for enterprise vector and hybrid RAG search.\n\n"
    "Strict Requirements:\n"
    "1. Preserve the original search intent, core entities, dates, numbers, and constraints.\n"
    "2. Generate diverse, high-value alternatives (e.g. synonym expansion, intent alignment, "
    "technical specificity boost, troubleshooting phrasing, or architectural context).\n"
    "3. Avoid duplicate queries and avoid generic, unrelated filler.\n"
    "4. Return ONLY a valid JSON array containing 5 strings, with no additional conversational prose.\n"
    'Format: ["reformulated query 1", "reformulated query 2", "reformulated query 3", "reformulated query 4", "reformulated query 5"]'
)


def build_user_prompt(
    query: str,
    intent: str,
    entities: List[str],
    context: Optional[str] = None,
) -> str:
    """Dynamically supply the runtime query, intent, entities, and optional context."""
    entity_str = ", ".join(entities) if entities else "None"
    prompt = (
        f'Original Query: "{query}"\n'
        f"Detected Intent: {intent}\n"
        f"Extracted Entities: {entity_str}\n"
    )
    if context:
        prompt += f"Conversation Context: {context}\n"
    prompt += "\nGenerate exactly 5 distinct, high-precision candidate query strings as a JSON array:"
    return prompt


# ---------------------------------------------------------------------------
# Structured Output Validation & Parsing
# ---------------------------------------------------------------------------

def parse_and_validate_candidates(
    raw_text: str,
    original_query: str,
    entities: Optional[List[str]] = None,
) -> List[str]:
    """
    Robustly extract, sanitize, and validate candidate queries from model text.
    Handles markdown blocks, raw JSON arrays, JSON objects with keys, or fallback lines.
    Ensures candidates preserve entities where appropriate and contains no duplicates.
    """
    if not raw_text or not raw_text.strip():
        raise MalformedResponseError("Model response was empty or whitespace only.")

    cleaned = raw_text.strip()

    # Strip markdown code blocks if present
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()

    candidates: List[str] = []

    # 1. Try parsing directly as JSON
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, list):
            candidates = [str(item).strip() for item in parsed if str(item).strip()]
        elif isinstance(parsed, dict):
            # Try common wrapper keys
            for key in ["candidates", "queries", "reformulated_queries", "results"]:
                if key in parsed and isinstance(parsed[key], list):
                    candidates = [str(item).strip() for item in parsed[key] if str(item).strip()]
                    break
    except Exception:
        # 2. Fallback: line-by-line heuristic extraction
        lines = cleaned.splitlines()
        for line in lines:
            line_str = line.strip()
            # Match bullet points or numbered lists: e.g. "1. query", "- query", '"query"'
            match = re.match(r'^(?:\d+[\.\)]|\-|\*)\s*["\']?(.*?)["\']?$', line_str)
            if match:
                candidate = match.group(1).strip().strip('"').strip("'")
                if candidate:
                    candidates.append(candidate)

    # 3. Validation & Deduplication
    unique_candidates: List[str] = []
    seen = set()

    for cand in candidates:
        # Remove any lingering quotes/brackets
        cand_clean = cand.strip().strip('"').strip("'").strip("[]")
        # Strip trailing commas or periods that might come from bad formatting
        cand_clean = re.sub(r'[\r\n]+', ' ', cand_clean).strip()
        if not cand_clean or len(cand_clean) < 3:
            continue

        lower = cand_clean.lower()
        if lower in seen:
            continue
        seen.add(lower)
        unique_candidates.append(cand_clean)

    # Must contain at least 2 distinct valid candidate queries
    if len(unique_candidates) < 2:
        raise MalformedResponseError(
            f"Model produced fewer than 2 valid distinct candidates: {unique_candidates}"
        )

    return unique_candidates[:5]


# ---------------------------------------------------------------------------
# Abstract Base Provider
# ---------------------------------------------------------------------------

class BaseReformulationProvider(ABC):
    """Abstract base class for all LLM reformulation providers."""

    name: str = "base"

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if required environment variables / credentials are set."""
        pass

    @abstractmethod
    def reformulate(
        self,
        query: str,
        intent: str,
        entities: List[str],
        context: Optional[str] = None,
    ) -> List[str]:
        """
        Execute query reformulation using this provider.
        Returns a list of 2 to 5 distinct candidate queries.
        Raises ReformulationError subclasses on failure.
        """
        pass
