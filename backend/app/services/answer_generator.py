import logging
import json
from typing import List, Dict, Any, Tuple
from app.core.config import settings

logger = logging.getLogger(__name__)


def call_gemini_rag_answer(query: str, top_passages: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Call Gemini API using google-genai SDK to generate a grounded answer with citations.
    """
    if not settings.GEMINI_API_KEY:
        return None, []

    try:
        from google import genai
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        passages_text = ""
        citations = []
        for idx, doc in enumerate(top_passages):
            cit_num = idx + 1
            cit_info = {
                "citation_id": f"[{cit_num}]",
                "filename": doc["filename"],
                "document_id": doc["document_id"],
                "chunk_index": doc["chunk_index"],
            }
            citations.append(cit_info)
            passages_text += f"\n--- Source [{cit_num}]: {doc['filename']} ---\n{doc['content']}\n"

        prompt = f"""You are an enterprise AI assistant answering a query based ONLY on the provided retrieved document passages below.

Strict Instructions:
1. Base your answer ONLY on the information in the provided passages. Do NOT make up information.
2. If the passages do NOT contain enough information to answer the user query, reply EXACTLY with: "No relevant information found."
3. Include inline numerical source citations like [1], [2] when referencing information.

User Query: "{query}"

Retrieved Passages:
{passages_text}

Provide a concise, professional answer with inline citations:"""

        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
        )

        if response and response.text:
            answer = response.text.strip()
            return answer, citations
    except Exception as e:
        logger.warning(f"Gemini RAG answer generation warning: {str(e)}")

    return None, []


def generate_fallback_rag_answer(query: str, top_passages: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Algorithmic RAG answer synthesis fallback when Gemini API key is not configured.
    Extracted key sentences matching query tokens with citations.
    """
    if not top_passages:
        return "No relevant information found.", []

    relevant_passages = [p for p in top_passages if p["relevance_score"] >= 0.50]
    if not relevant_passages:
        return "No relevant information found.", []

    answer_parts = []
    citations = []

    for idx, doc in enumerate(relevant_passages[:3]):
        cit_num = idx + 1
        cit_info = {
            "citation_id": f"[{cit_num}]",
            "filename": doc["filename"],
            "document_id": doc["document_id"],
            "chunk_index": doc["chunk_index"],
        }
        citations.append(cit_info)

        snippet = doc["highlighted_snippet"] or doc["content"][:200]
        answer_parts.append(f"{snippet.strip()} [{cit_num}]")

    summary_text = " ".join(answer_parts)
    answer = f"Based on retrieved enterprise documents: {summary_text}"
    return answer, citations


class AIAnswerGeneratorService:
    def generate_answer(self, query: str, top_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Synthesize grounded concise answer from Top 5 reranked document passages.
        Returns "No relevant information found." if documents are insufficient.
        """
        if not top_results or len(top_results) == 0:
            return {
                "answer": "No relevant information found.",
                "has_answer": False,
                "confidence_score": 0.0,
                "citations": []
            }

        top_5 = top_results[:5]
        max_relevance = max(doc["relevance_score"] for doc in top_5)

        # Check threshold
        if max_relevance < 0.45:
            return {
                "answer": "No relevant information found.",
                "has_answer": False,
                "confidence_score": max_relevance,
                "citations": []
            }

        # Call Gemini AI
        gemini_answer, citations = call_gemini_rag_answer(query, top_5)

        if not gemini_answer:
            logger.info("[ANSWER] Gemini API key not configured or call failed. Using algorithmic grounded answer fallback.")
            gemini_answer, citations = generate_fallback_rag_answer(query, top_5)
        else:
            logger.info(f"[ANSWER] Gemini 2.5 Flash generated grounded RAG answer with {len(citations)} citations.")

        has_answer = "No relevant information found." not in gemini_answer

        logger.info(f"[ANSWER] Grounded answer generated (has_answer={has_answer}, citations={len(citations)})")

        return {
            "answer": gemini_answer,
            "has_answer": has_answer,
            "confidence_score": max_relevance,
            "citations": citations
        }


ai_answer_generator_service = AIAnswerGeneratorService()

