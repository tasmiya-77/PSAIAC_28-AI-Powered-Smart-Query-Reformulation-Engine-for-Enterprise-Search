import re
import time
import logging
import json
from typing import List, Dict, Any, Tuple, Optional
from app.core.config import settings
from app.schemas.query import CandidateQuery, QueryExplainability

logger = logging.getLogger(__name__)

# Common tech typos dictionary for spell correction & acronym mapping
TECH_SPELL_MAP = {
    "postgres": "PostgreSQL",
    "postgresl": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "fastpi": "FastAPI",
    "fast-api": "FastAPI",
    "chromdb": "ChromaDB",
    "chromadb": "ChromaDB",
    "reag": "RAG",
    "rag": "Retrieval Augmented Generation (RAG)",
    "nextjs": "Next.js",
    "next-js": "Next.js",
    "pydantc": "Pydantic",
    "pydantic": "Pydantic",
    "tailwind": "Tailwind CSS",
    "shadcn": "shadcn/ui",
}

# General-vocabulary conservative spell correction dictionary.
# Only common, unambiguous single-character transpositions/deletions are listed.
# Words that are genuinely ambiguous (could be multiple real words) are intentionally omitted.
GENERAL_SPELL_MAP = {
    "reume": "resume",
    "recieve": "receive",
    "occured": "occurred",
    "occurance": "occurrence",
    "seperate": "separate",
    "definately": "definitely",
    "accomodate": "accommodate",
    "begining": "beginning",
    "beleive": "believe",
    "calender": "calendar",
    "comming": "coming",
    "committment": "commitment",
    "concious": "conscious",
    "existance": "existence",
    "grammer": "grammar",
    "independant": "independent",
    "millenium": "millennium",
    "neccessary": "necessary",
    "privelege": "privilege",
    "reccomend": "recommend",
    "relevent": "relevant",
    "resposible": "responsible",
    "succesful": "successful",
    "tommorow": "tomorrow",
    "untill": "until",
    "wierd": "weird",
    "writting": "writing",
    "analysys": "analysis",
    "requrement": "requirement",
    "managment": "management",
    "documentaion": "documentation",
    "performace": "performance",
    "implmentation": "implementation",
    "integartion": "integration",
    "configration": "configuration",
    "autentication": "authentication",
    "authoriation": "authorization",
}


def normalize_and_clean_query(raw_query: str) -> str:
    """Step 1: Strip formatting, normalize whitespace, and trim unwanted punctuation."""
    cleaned = re.sub(r"\s+", " ", raw_query).strip()
    cleaned = re.sub(r"[^\w\s\-\.\?\/]", "", cleaned)
    return cleaned


def correct_spelling_and_acronyms(query: str) -> Tuple[str, List[str]]:
    """Step 2: Correct tech typos/acronyms AND common general-vocabulary typos.
    
    Tech corrections are always applied silently (they are unambiguous expansions).
    General corrections are only applied when the misspelling has no other plausible
    interpretation (conservative list). The corrected_terms list records every change
    so the caller can surface it to the user if needed.
    """
    words = query.split()
    corrected_words = []
    corrected_terms = []

    for word in words:
        lowered = word.lower()
        if lowered in TECH_SPELL_MAP:
            corrected_val = TECH_SPELL_MAP[lowered]
            corrected_words.append(corrected_val)
            if corrected_val.lower() != lowered:
                corrected_terms.append(f"{word} -> {corrected_val}")
        elif lowered in GENERAL_SPELL_MAP:
            corrected_val = GENERAL_SPELL_MAP[lowered]
            corrected_words.append(corrected_val)
            corrected_terms.append(f"{word} -> {corrected_val}")
        else:
            corrected_words.append(word)

    return " ".join(corrected_words), corrected_terms


def detect_query_intent(query: str) -> str:
    """Step 3: Detect query intent (TROUBLESHOOTING, TECHNICAL_SEARCH, CONCEPTUAL_EXPLANATION, COMPARISON)."""
    lowered = query.lower()
    word_count = len(lowered.split())

    # Troubleshooting keywords — highest priority
    if any(k in lowered for k in ["error", "fix", "issue", "bug", "crash", "latency", "slow", "fail", "timeout", "exception", "not working", "broken"]):
        return "TROUBLESHOOTING"

    # Comparison intent
    if any(k in lowered for k in ["vs", "versus", "difference", "compare", "benchmark", "pros and cons", "trade-off"]):
        return "COMPARISON"

    # Conceptual / architectural explanation
    if any(k in lowered for k in ["what is", "how does", "architecture", "overview", "explain", "concept", "definition", "meaning of"]):
        return "CONCEPTUAL_EXPLANATION"

    # Document / content retrieval signals (find, search, look up, show)
    if any(k in lowered for k in ["find", "search for", "look up", "show me", "list", "get", "fetch", "retrieve", "document"]):
        return "DOCUMENT_SEARCH"

    # Technical search — requires at least one recognized tech indicator
    tech_indicators = [
        "api", "sdk", "database", "server", "backend", "frontend", "deploy",
        "install", "setup", "config", "configure", "integration", "framework",
        "library", "package", "module", "code", "script", "query", "index",
        "endpoint", "request", "response", "authentication", "authorization",
    ]
    if any(k in lowered for k in tech_indicators):
        return "TECHNICAL_SEARCH"

    # Short queries with no technical signals → general search
    if word_count <= 3:
        return "GENERAL_SEARCH"

    return "TECHNICAL_SEARCH"


def extract_entities_and_keywords(query: str) -> Tuple[List[str], List[str]]:
    """Step 4: Extract technical entities and key search domain tokens."""
    known_tech = [
        "PostgreSQL", "FastAPI", "ChromaDB", "Next.js", "Python", "TypeScript",
        "React", "RAG", "Vector", "Embedding", "Pydantic", "Tailwind", "Docker"
    ]
    
    found_entities = []
    for tech in known_tech:
        if re.search(r"\b" + re.escape(tech) + r"\b", query, re.IGNORECASE):
            found_entities.append(tech)

    # Keywords (words longer than 3 chars excluding stop words)
    stop_words = {"how", "to", "fix", "the", "and", "is", "for", "with", "in", "on", "a", "an", "of", "what"}
    tokens = re.findall(r"\b[a-zA-Z]{3,}\b", query)
    keywords = [t for t in tokens if t.lower() not in stop_words and t not in found_entities]

    return found_entities, keywords


def call_gemini_query_reformulation(
    query: str, intent: str, entities: List[str]
) -> Optional[List[str]]:
    """
    Step 5: Call Gemini API using google-genai SDK if GEMINI_API_KEY is available.
    Generates 5 distinct high-precision candidate query reformulations.
    """
    if not settings.GEMINI_API_KEY:
        return None

    try:
        from google import genai
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        prompt = f"""You are an expert AI search engine engineer.
Given the following user search query, generate exactly 5 distinct, high-precision reformulated query candidates optimized for vector database RAG search.

Original Query: "{query}"
Detected Intent: {intent}
Extracted Entities: {', '.join(entities) if entities else 'None'}

Return ONLY a valid JSON array of 5 strings representing the candidate queries.
Example output format:
["candidate query 1", "candidate query 2", "candidate query 3", "candidate query 4", "candidate query 5"]
"""

        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
        )

        if response and response.text:
            cleaned_text = response.text.strip()
            if "```json" in cleaned_text:
                cleaned_text = cleaned_text.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_text:
                cleaned_text = cleaned_text.split("```")[1].split("```")[0].strip()
                
            candidates = json.loads(cleaned_text)
            if isinstance(candidates, list) and len(candidates) >= 3:
                return [str(c).strip() for c in candidates[:5]]
    except Exception as e:
        logger.warning(f"Gemini API query reformulation call skipped/failed: {str(e)}")

    return None


def _strip_leading_verb(query: str, verbs: List[str]) -> str:
    """Remove a leading action verb from a query to avoid doubled phrases.
    e.g. strip_leading_verb('fix timeout error', ['fix']) → 'timeout error'
    Only strips a single leading word when it exactly matches one of the given verbs.
    """
    parts = query.split(None, 1)
    if len(parts) > 1 and parts[0].lower() in verbs:
        return parts[1]
    return query


def generate_fallback_candidate_queries(
    query: str, intent: str, entities: List[str], keywords: List[str]
) -> List[str]:
    """
    Step 5 (Fallback): Algorithmic candidate expansion if Gemini API key is omitted.
    Generates 5 distinct, intent-specific search rewrites without blindly appending
    generic technical suffixes to every query.
    """
    entity_str = " ".join(entities) if entities else ""
    kw_str = " ".join(keywords[:3]) if keywords else query

    if intent == "TROUBLESHOOTING":
        # Strip leading fix/resolve so we don't produce "How to fix fix …"
        core = _strip_leading_verb(query, ["fix", "resolve", "repair", "debug", "address"])
        c1 = f"How to fix {core}"
        c2 = f"{core} error resolution and root cause analysis"
        c3 = f"Troubleshooting guide for {core} failure"
        c4 = f"{query} known issues workaround and patch"
        c5 = f"Stack trace debugging {entity_str} {kw_str} problem".strip()

    elif intent == "COMPARISON":
        c1 = f"{query} comparison and evaluation"
        c2 = f"Differences between {query} — pros and cons"
        c3 = f"Benchmark and trade-off analysis of {query}"
        c4 = f"Which is better: {query} — decision guide"
        c5 = f"{query} feature matrix and use-case suitability"

    elif intent == "CONCEPTUAL_EXPLANATION":
        # Strip leading "what is / how does" to avoid "Explanation of what is …"
        core = _strip_leading_verb(query, ["what", "how", "why", "when", "where"])
        c1 = f"Explanation of {core} concepts and principles"
        c2 = f"What is {core} and how does it work"
        c3 = f"{core} architecture overview and fundamentals"
        c4 = f"Deep dive into {core} design and theory"
        c5 = f"Beginner guide to understanding {core}"

    elif intent == "DOCUMENT_SEARCH":
        # Strip leading find/search/get so we don't produce "Documents related to find …"
        core = _strip_leading_verb(query, ["find", "search", "get", "fetch", "retrieve", "show", "list"])
        c1 = f"Documents related to {core}"
        c2 = f"Find {core} report or record"
        c3 = f"{core} official documentation and reference material"
        c4 = f"Search results for {core} in enterprise knowledge base"
        c5 = f"{kw_str} files and content matching {core}".strip()

    elif intent == "GENERAL_SEARCH":
        # Short, generic or non-technical queries: broaden without adding tech jargon
        c1 = f"{query}"
        c2 = f"{query} overview and summary"
        c3 = f"Information about {query}"
        c4 = f"{query} examples and use cases"
        c5 = f"Find documents mentioning {query}"

    else:  # TECHNICAL_SEARCH — only add tech context if there are entities/keywords
        if entities:
            tech_context = entity_str
        elif kw_str:
            tech_context = kw_str
        else:
            tech_context = query

        c1 = f"{query} technical reference and API documentation"
        c2 = f"{query} implementation examples and code usage"
        c3 = f"{tech_context} configuration and setup guide"
        c4 = f"Best practices for {query} in production environments"
        c5 = f"{query} integration patterns and architecture decisions"

    return [c1, c2, c3, c4, c5]


def score_and_rank_candidates(
    original_query: str, candidates: List[str], intent: str, entities: List[str]
) -> List[CandidateQuery]:
    """Step 6: Rank candidate queries and assign confidence scores (0.0 - 1.0)."""
    ranked: List[CandidateQuery] = []
    
    strategies = [
        "intent_alignment_expansion",
        "semantic_domain_enrichment",
        "keyword_specificity_boost",
        "vector_embedding_optimization",
        "contextual_term_weighting"
    ]

    for idx, cand in enumerate(candidates):
        # Calculate heuristic match score
        score = 0.82 + (0.03 * (4 - idx))
        
        # Entity overlap bonus
        for ent in entities:
            if ent.lower() in cand.lower():
                score += 0.02

        # Cap score between 0.70 and 0.98
        score = min(0.98, max(0.70, round(score, 2)))
        
        strategy = strategies[idx % len(strategies)]
        ranked.append(CandidateQuery(
            query=cand,
            rank=idx + 1,
            score=score,
            strategy=strategy
        ))

    # Sort by score descending
    ranked.sort(key=lambda x: x.score, reverse=True)
    
    # Re-index ranks
    for idx, item in enumerate(ranked):
        item.rank = idx + 1

    return ranked


def process_query_pipeline(
    raw_query: str,
    mode: str = "hybrid",
    context: Optional[str] = None,
) -> QueryExplainability:
    """
    Execute full Query Processing Pipeline:
    Normalize -> Spell Check -> Intent Detection -> Entity Extraction ->
    Dynamic Multi-LLM Reformulation (Groq -> Cloudflare -> Gemini -> Ollama Local -> Fallback) ->
    Candidate Scoring -> Explainability.
    """
    start_time = time.time()

    # 1. Normalize & Clean
    cleaned = normalize_and_clean_query(raw_query)

    # 2. Spell Correction
    corrected, corrected_terms = correct_spelling_and_acronyms(cleaned)

    # 3. Intent Detection
    intent = detect_query_intent(corrected)

    # 4. Entity & Keyword Extraction
    entities, keywords = extract_entities_and_keywords(corrected)

    logger.info(f"[QUERY_PIPELINE] Raw Query: '{raw_query}' -> Cleaned: '{corrected}' | Intent: {intent} | Entities: {entities}")

    # 5. Dynamic Multi-LLM Reformulation with local Ollama & algorithmic fallback
    from app.services.reformulation import multi_llm_reformulation_service

    candidates_raw, provider_used = multi_llm_reformulation_service.reformulate(
        query=corrected,
        intent=intent,
        entities=entities,
        context=context,
    )

    if not candidates_raw:
        logger.info("[QUERY_PIPELINE] LLM providers unavailable. Generating algorithmic fallback candidate reformulations.")
        candidates_raw = generate_fallback_candidate_queries(corrected, intent, entities, keywords)
        provider_used = "Algorithmic Fallback"
    else:
        logger.info(f"[QUERY_PIPELINE] {provider_used} generated {len(candidates_raw)} candidate query reformulations.")

    # 6. Candidate Ranking
    ranked_candidates = score_and_rank_candidates(corrected, candidates_raw, intent, entities)
    best_candidate = ranked_candidates[0]

    logger.info(f"[QUERY_PIPELINE] Best Reformulated Query selected: '{best_candidate.query}' (Score: {best_candidate.score})")

    # Added keywords list
    added_keywords = list(set(keywords + [w.lower() for w in best_candidate.query.split() if len(w) > 4 and w.lower() not in raw_query.lower()]))[:5]

    # 7. Short Explanation
    spell_note = ""
    if corrected_terms:
        spell_note = f" Spelling corrected: {'; '.join(corrected_terms)}."

    intent_labels = {
        "TROUBLESHOOTING": "troubleshooting / error resolution",
        "COMPARISON": "comparison and evaluation",
        "CONCEPTUAL_EXPLANATION": "conceptual explanation",
        "DOCUMENT_SEARCH": "document retrieval",
        "GENERAL_SEARCH": "general information search",
        "TECHNICAL_SEARCH": "technical search",
    }
    intent_label = intent_labels.get(intent, intent.lower().replace("_", " "))

    if provider_used and provider_used != "Algorithmic Fallback":
        explanation = (
            f"Query reformulated via {provider_used} for {intent_label}."
            f"{spell_note}"
            f" Enriched with: {', '.join(entities) if entities else 'semantic context'}."
        )
    else:
        if entities:
            enrichment = f"entities: {', '.join(entities)}"
        elif corrected_terms:
            enrichment = "corrected vocabulary"
        else:
            enrichment = "semantic keyword expansion"
        explanation = (
            f"Algorithmically expanded for {intent_label}.{spell_note} Enriched with {enrichment}."
        )

    return QueryExplainability(
        original_query=raw_query,
        cleaned_query=corrected,
        best_query=best_candidate.query,
        candidate_queries=ranked_candidates,
        intent=intent,
        entities=entities,
        added_keywords=added_keywords,
        confidence_score=best_candidate.score,
        explanation=explanation,
        provider_used=provider_used,
    )


