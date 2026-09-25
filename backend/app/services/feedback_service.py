import os
import json
import uuid
import time
import threading
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.schemas.feedback import (
    FeedbackSubmissionRequest,
    FeedbackSubmissionResponse,
    FeedbackStatsResponse,
    UsefulDocumentItem,
    QuerySuccessItem,
)

logger = logging.getLogger(__name__)

FEEDBACK_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "feedback_store.json")
_feedback_lock = threading.Lock()


class FeedbackService:
    def __init__(self, file_path: str = FEEDBACK_FILE_PATH):
        self.file_path = file_path
        self._ensure_storage_exists()

    def _ensure_storage_exists(self):
        """Ensure file directory and storage JSON file exist."""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _load_feedback(self) -> List[Dict[str, Any]]:
        """Load feedback entries from JSON file safely."""
        self._ensure_storage_exists()
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"[FEEDBACK] Error reading feedback file: {str(e)}")
            return []

    def _save_feedback(self, entries: List[Dict[str, Any]]) -> bool:
        """Save feedback entries to JSON file cleanly."""
        self._ensure_storage_exists()
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(entries, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"[FEEDBACK] Error saving feedback file: {str(e)}")
            return False

    def submit_feedback(self, request: FeedbackSubmissionRequest) -> FeedbackSubmissionResponse:

        """
        Store a new feedback entry. Prevents exact duplicate submissions within a short timeframe.
        """
        rating_clean = request.rating.lower().strip()
        if rating_clean not in ["helpful", "not_helpful"]:
            raise ValueError("Rating must be 'helpful' or 'not_helpful'")

        feedback_id = f"fb_{uuid.uuid4().hex[:10]}"
        now_iso = datetime.utcnow().isoformat() + "Z"

        entry = {
            "feedback_id": feedback_id,
            "query": request.query.strip(),
            "reformulated_query": request.reformulated_query or request.query.strip(),
            "document_id": request.document_id,
            "chunk_id": request.chunk_id or f"{request.document_id}_chunk_0",
            "filename": request.filename or request.document_id,
            "rating": rating_clean,
            "feedback_text": request.feedback_text.strip() if request.feedback_text else None,
            "timestamp": now_iso,
        }

        with _feedback_lock:
            entries = self._load_feedback()

            # Duplicate check: check if same query + document_id + rating was submitted recently
            for existing in entries:
                if (
                    existing.get("query", "").lower() == entry["query"].lower()
                    and existing.get("document_id") == entry["document_id"]
                    and existing.get("rating") == entry["rating"]
                ):
                    logger.info(f"[FEEDBACK] Duplicate feedback ignored for doc '{entry['document_id']}'")
                    return FeedbackSubmissionResponse(
                        success=True,
                        message="Feedback already recorded for this result.",
                        feedback_id=existing.get("feedback_id", feedback_id),
                    )

            entries.insert(0, entry)
            self._save_feedback(entries)

        logger.info(f"[FEEDBACK] Recorded '{rating_clean}' feedback for doc '{request.document_id}' (Query: '{request.query}')")
        return FeedbackSubmissionResponse(
            success=True,
            message="Thank you for your feedback!",
            feedback_id=feedback_id,
        )

    def get_feedback_stats(self) -> FeedbackStatsResponse:
        """
        Compute feedback analytics: Helpful Rate, Not-Helpful Rate, Query Success Rankings, Most Useful Documents.
        """
        with _feedback_lock:
            entries = self._load_feedback()

        total = len(entries)
        if total == 0:
            return FeedbackStatsResponse(
                total_feedback_count=0,
                helpful_count=0,
                not_helpful_count=0,
                helpful_rate_percentage=0.0,
                not_helpful_rate_percentage=0.0,
                most_useful_documents=[],
                highest_success_queries=[],
                lowest_success_queries=[],
                recent_feedback_comments=[],
            )

        helpful_count = sum(1 for e in entries if e.get("rating") == "helpful")
        not_helpful_count = sum(1 for e in entries if e.get("rating") == "not_helpful")

        helpful_rate = round((helpful_count / total) * 100.0, 1)
        not_helpful_rate = round((not_helpful_count / total) * 100.0, 1)

        # Document aggregations
        doc_map: Dict[str, Dict[str, Any]] = {}
        for e in entries:
            doc_id = e.get("document_id", "unknown")
            fname = e.get("filename") or doc_id
            if doc_id not in doc_map:
                doc_map[doc_id] = {
                    "document_id": doc_id,
                    "filename": fname,
                    "helpful_count": 0,
                    "not_helpful_count": 0,
                }
            if e.get("rating") == "helpful":
                doc_map[doc_id]["helpful_count"] += 1
            elif e.get("rating") == "not_helpful":
                doc_map[doc_id]["not_helpful_count"] += 1

        useful_docs: List[UsefulDocumentItem] = []
        for doc_id, data in doc_map.items():
            doc_total = data["helpful_count"] + data["not_helpful_count"]
            sat_rate = round((data["helpful_count"] / max(1, doc_total)) * 100.0, 1)
            useful_docs.append(
                UsefulDocumentItem(
                    document_id=doc_id,
                    filename=data["filename"],
                    helpful_count=data["helpful_count"],
                    not_helpful_count=data["not_helpful_count"],
                    satisfaction_rate=sat_rate,
                )
            )

        # Sort docs by helpful count descending
        useful_docs.sort(key=lambda d: (d.helpful_count, d.satisfaction_rate), reverse=True)

        # Query aggregations
        query_map: Dict[str, Dict[str, Any]] = {}
        for e in entries:
            q_text = e.get("query", "Unknown").strip()
            if not q_text:
                continue
            if q_text not in query_map:
                query_map[q_text] = {"query": q_text, "total": 0, "helpful": 0}
            query_map[q_text]["total"] += 1
            if e.get("rating") == "helpful":
                query_map[q_text]["helpful"] += 1

        query_items: List[QuerySuccessItem] = []
        for q_text, q_data in query_map.items():
            succ_rate = round((q_data["helpful"] / float(q_data["total"])) * 100.0, 1)
            query_items.append(
                QuerySuccessItem(
                    query=q_text,
                    total_feedback=q_data["total"],
                    helpful_count=q_data["helpful"],
                    success_rate=succ_rate,
                )
            )

        highest_queries = sorted(query_items, key=lambda q: (q.success_rate, q.total_feedback), reverse=True)[:5]
        lowest_queries = sorted(query_items, key=lambda q: (q.success_rate, -q.total_feedback))[:5]

        # Recent comments
        recent_comments = [
            {
                "feedback_id": e["feedback_id"],
                "query": e["query"],
                "filename": e.get("filename", e["document_id"]),
                "rating": e["rating"],
                "comment": e["feedback_text"],
                "timestamp": e["timestamp"][:16].replace("T", " "),
            }
            for e in entries
            if e.get("feedback_text")
        ][:10]

        return FeedbackStatsResponse(
            total_feedback_count=total,
            helpful_count=helpful_count,
            not_helpful_count=not_helpful_count,
            helpful_rate_percentage=helpful_rate,
            not_helpful_rate_percentage=not_helpful_rate,
            most_useful_documents=useful_docs[:5],
            highest_success_queries=highest_queries,
            lowest_success_queries=lowest_queries,
            recent_feedback_comments=recent_comments,
        )


feedback_service = FeedbackService()
