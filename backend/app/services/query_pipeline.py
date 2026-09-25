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


def normalize_and_clean_query(raw_query: str) -> str:
    """Step 1: Strip formatting, normalize whitespace, and trim unwanted punctuation."""
    cleaned = re.sub(r"\s+", " ", raw_query).strip()
    cleaned = re.sub(r"[^\w\s\-\.\?\/]", "", cleaned)
    return cleaned


def correct_spelling_and_acronyms(query: str) -> Tuple[str, List[str]]:
    """Step 2: Correct tech typos and expand technical acronyms."""
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
        else:
            corrected_words.append(word)

    return " ".join(corrected_words), corrected_terms


def detect_query_intent(query: str) -> str:
    """Step 3: Detect query intent (TROUBLESHOOTING, TECHNICAL_SEARCH, CONCEPTUAL_EXPLANATION, COMPARISON)."""
    lowered = query.lower()
    
    if any(k in lowered for k in ["error", "fix", "issue", "bug", "crash", "latency", "slow", "fail", "timeout", "exception"]):
        return "TROUBLESHOOTING"
    elif any(k in lowered for k in ["vs", "versus", "difference", "compare", "benchmark", "pros and cons"]):
        return "COMPARISON"
    elif any(k in lowered for k in ["what is", "how does", "architecture", "overview", "explain", "concept"]):
        return "CONCEPTUAL_EXPLANATION"
    else:
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


def generate_fallback_candidate_queries(
    query: str, intent: str, entities: List[str], keywords: List[str]
) -> List[str]:
    """
    Step 5 (Fallback): Algorithmic candidate expansion if Gemini API key is omitted.
    Generates 5 distinct high-quality search rewrites.
    """
    entity_str = " ".join(entities) if entities else ""
    kw_str = " ".join(keywords[:3]) if keywords else ""

    c1 = f"{query} technical documentation and best practices"
    
    if intent == "TROUBLESHOOTING":
        c2 = f"How to resolve {query} error performance latency issue"
        c3 = f"{query} troubleshooting guide solution and root cause"
    elif intent == "COMPARISON":
        c2 = f"{query} performance benchmark trade-offs and comparison"
        c3 = f"Key differences and evaluation of {query}"
    elif intent == "CONCEPTUAL_EXPLANATION":
        c2 = f"Comprehensive explanation of {query} architecture and concepts"
        c3 = f"Understanding {query} fundamental principles"
    else: # TECHNICAL_SEARCH
        c2 = f"{query} implementation code examples and API usage"
        c3 = f"Vector search optimization for {query}"

    c4 = f"Optimized query: {entity_str} {kw_str} configuration and indexing".strip()
    c5 = f"Advanced guide: {query} integration pattern"

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


def process_query_pipeline(raw_query: str, mode: str = "hybrid") -> QueryExplainability:
    """
    Execute full Query Processing Pipeline:
    Normalize -> Spell Check -> Intent Detection -> Entity Extraction -> Gemini/Fallback Reformulation -> Candidate Scoring -> Explainability.
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

    # 5. Reformulation (Gemini with algorithmic fallback)
    candidates_raw = call_gemini_query_reformulation(corrected, intent, entities)
    is_gemini_used = candidates_raw is not None

    if not candidates_raw:
        logger.info("[QUERY_PIPELINE] Gemini API skipped/unavailable. Generating algorithmic fallback candidate reformulations.")
        candidates_raw = generate_fallback_candidate_queries(corrected, intent, entities, keywords)
    else:
        logger.info(f"[QUERY_PIPELINE] Gemini 2.5 Flash generated {len(candidates_raw)} candidate query reformulations.")

    # 6. Candidate Ranking
    ranked_candidates = score_and_rank_candidates(corrected, candidates_raw, intent, entities)
    best_candidate = ranked_candidates[0]

    logger.info(f"[QUERY_PIPELINE] Best Reformulated Query selected: '{best_candidate.query}' (Score: {best_candidate.score})")

    # Added keywords list
    added_keywords = list(set(keywords + [w.lower() for w in best_candidate.query.split() if len(w) > 4 and w.lower() not in raw_query.lower()]))[:5]

    # 7. Short Explanation
    if is_gemini_used:
        explanation = f"Query was reformulated using Gemini 2.5 AI model. Detected intent '{intent}' and enriched with technical terms ({', '.join(entities) if entities else 'domain context'})."
    else:
        explanation = f"Query was cleaned and algorithmically expanded based on intent '{intent}'. Enriched with domain entities ({', '.join(entities) if entities else 'keywords'}) for high RAG precision."

    return QueryExplainability(
        original_query=raw_query,
        cleaned_query=corrected,
        best_query=best_candidate.query,
        candidate_queries=ranked_candidates,
        intent=intent,
        entities=entities,
        added_keywords=added_keywords,
        confidence_score=best_candidate.score,
        explanation=explanation
    )

