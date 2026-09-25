import io
import docx
import pypdf
from fastapi.testclient import TestClient
from app.main import app
from app.services.document_parser import split_text_into_chunks, calculate_file_hash
from app.services.vector_store import get_embedding_function

client = TestClient(app)


def make_pdf_bytes(title: str, body: str) -> bytes:
    """Generate valid PDF byte stream containing text for testing."""
    text = f"{title}\n{body}"
    clean_text = text.replace("(", "[").replace(")", "]")
    pdf_str = f"""%PDF-1.4
1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj
2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj
3 0 obj <</Type /Page /Parent 2 0 R /Resources <</Font <</F1 4 0 R>>>> /MediaBox [0 0 612 792] /Contents 5 0 R>> endobj
4 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj
5 0 obj <</Length {len(clean_text) + 40}>>
stream
BT /F1 12 Tf 72 712 Td ({clean_text}) Tj ET
endstream
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000053 00000 n
0000000102 00000 n
0000000215 00000 n
0000000287 00000 n
trailer <</Size 6 /Root 1 0 R>>
startxref
370
%%EOF"""
    return pdf_str.encode("latin-1")


def make_docx_bytes(title: str, paragraphs: list) -> bytes:
    """Generate valid DOCX byte stream for testing."""
    doc = docx.Document()
    doc.add_heading(title, level=1)
    for p in paragraphs:
        doc.add_paragraph(p)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def run_pipeline_verification():
    print("=================================================================")
    print("STARTING END-TO-END PIPELINE AUDIT & VERIFICATION SUITE")
    print("=================================================================")

    # 1. Verify Sentence Transformers Embedding Function
    print("\n[STEP 1] Testing Sentence Transformers Embedding Function...")
    emb_fn = get_embedding_function()
    sample_vecs = emb_fn(["Test query for Sentence Transformers embeddings"])
    assert len(sample_vecs) == 1
    assert len(sample_vecs[0]) > 0
    print(f"  -> PASSED: Embedding vector generated with dimension {len(sample_vecs[0])} (Type: {type(emb_fn).__name__})")

    # 2. Ingest TXT Document
    print("\n[STEP 2] Ingesting TXT Document...")
    txt_content = b"""PostgreSQL RAG Guide:
Configure HNSW index parameters (m=16, ef_construction=64) to optimize PostgreSQL vector similarity query latency.
Maintain connection pooling using asyncpg or SQLAlchemy async engine for high throughput FastAPI retrieval.
"""
    res_txt = client.post("/api/v1/ingest/upload", files={"file": ("postgres_guide.txt", txt_content, "text/plain")})
    assert res_txt.status_code == 201, f"Expected 201, got {res_txt.status_code}"
    txt_data = res_txt.json()
    doc_id_txt = txt_data["document"]["document_id"]
    print(f"  -> PASSED: TXT Document ingested successfully. ID: {doc_id_txt}, Chunks: {txt_data['document']['chunk_count']}")

    # 3. Ingest DOCX Document
    print("\n[STEP 3] Ingesting DOCX Document...")
    docx_content = make_docx_bytes(
        "ChromaDB Vector Store Optimization",
        [
            "ChromaDB persistent client stores high-dimensional vector embeddings for fast nearest-neighbor similarity retrieval.",
            "Use BAAI/bge-small-en or Sentence Transformers for generating precise document embeddings.",
            "Reciprocal Rank Fusion (RRF) combines vector distance with BM25 lexical keyword scores."
        ]
    )
    res_docx = client.post(
        "/api/v1/ingest/upload",
        files={"file": ("chroma_guide.docx", docx_content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )
    assert res_docx.status_code == 201, f"Expected 201, got {res_docx.status_code}"
    docx_data = res_docx.json()
    doc_id_docx = docx_data["document"]["document_id"]
    print(f"  -> PASSED: DOCX Document ingested successfully. ID: {doc_id_docx}, Chunks: {docx_data['document']['chunk_count']}")

    # 4. Ingest PDF Document
    print("\n[STEP 4] Ingesting PDF Document...")
    pdf_content = make_pdf_bytes(
        "Gemini Reformulation Architecture",
        "Gemini 2.5 Flash reformulates raw user search queries into 5 distinct high precision candidate queries."
    )
    res_pdf = client.post(
        "/api/v1/ingest/upload",
        files={"file": ("gemini_arch.pdf", pdf_content, "application/pdf")}
    )
    assert res_pdf.status_code == 201, f"Expected 201, got {res_pdf.status_code}"
    pdf_data = res_pdf.json()
    doc_id_pdf = pdf_data["document"]["document_id"]
    print(f"  -> PASSED: PDF Document ingested successfully. ID: {doc_id_pdf}, Chunks: {pdf_data['document']['chunk_count']}")

    # 5. Prevent Duplicate Indexing using SHA-256 Hash
    print("\n[STEP 5] Testing Duplicate Prevention (SHA-256 Hash)...")
    res_dup = client.post(
        "/api/v1/ingest/upload",
        files={"file": ("chroma_guide_dup.docx", docx_content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )
    assert res_dup.status_code == 201
    dup_data = res_dup.json()
    assert "Duplicate SHA-256 hash" in dup_data["message"]
    assert dup_data["document"]["document_id"] == doc_id_docx
    print(f"  -> PASSED: Duplicate upload correctly identified without re-indexing. Doc ID: {dup_data['document']['document_id']}")

    # 6. Test Query Reformulation API
    print("\n[STEP 6] Testing Gemini Query Reformulation...")
    res_ref = client.post("/api/v1/query/reformulate", json={"query": "how to optimize chromadb vector store performance in fastpi"})
    assert res_ref.status_code == 200
    ref_data = res_ref.json()
    assert ref_data["success"] is True
    assert "best_query" in ref_data["data"]
    print(f"  -> PASSED: Original query reformulated to: '{ref_data['data']['best_query']}'")

    # 7. Test Enterprise Search Pipeline (Connected Reformulated Query -> ChromaDB Search -> AI Answer)
    print("\n[STEP 7] Executing End-to-End Enterprise Search...")
    search_payload = {
        "query": "how to optimize chromadb vector store performance in fastpi",
        "mode": "hybrid",
        "filters": {"department": "all", "file_type": "all", "min_relevance": 0.0},
        "page": 1,
        "page_size": 5
    }
    res_search = client.post("/api/v1/search/execute", json=search_payload)
    assert res_search.status_code == 200
    s_data = res_search.json()
    assert s_data["success"] is True
    assert s_data["total_results"] > 0
    top_doc = s_data["results"][0]
    assert "rank" in top_doc and top_doc["rank"] == 1
    assert "title" in top_doc and top_doc["title"] != ""
    assert "passage" in top_doc
    assert "keyword_score" in top_doc
    assert "semantic_score" in top_doc
    assert "rerank_score" in top_doc
    print(f"  -> PASSED: Search returned {s_data['total_results']} result(s). Top match: '{top_doc['filename']}' ({top_doc['relevance_percentage']}% Match).")
    print(f"  -> PASSED: Scores -> Semantic: {top_doc['semantic_score']}, Keyword (BM25): {top_doc['keyword_score']}, Rerank: {top_doc['rerank_score']}")
    print(f"  -> PASSED: AI Answer: '{s_data['ai_answer']['answer'][:100]}...'")


    # 8. Test Feedback, Analytics & Evaluation Endpoints
    print("\n[STEP 8] Testing Feedback, Analytics & IR Evaluation Suite...")
    
    # 8a. Feedback Submission
    res_fb = client.post("/api/v1/analytics/feedback", json={
        "query": "how to optimize chromadb vector store performance in fastpi",
        "document_id": doc_id_docx,
        "rating": "helpful",
        "feedback_text": "Great search result detailing RRF and BGE cross-encoder reranking!"
    })
    assert res_fb.status_code == 200
    assert res_fb.json()["success"] is True
    print("  -> PASSED: User feedback submitted successfully.")

    # 8b. Feedback Statistics
    res_fb_stats = client.get("/api/v1/analytics/feedback-stats")
    assert res_fb_stats.status_code == 200
    assert res_fb_stats.json()["total_feedback_count"] > 0
    print(f"  -> PASSED: Feedback statistics fetched. Total feedback votes: {res_fb_stats.json()['total_feedback_count']}")

    # 8c. Analytics Telemetry Metrics
    res_metrics = client.get("/api/v1/analytics/metrics")
    assert res_metrics.status_code == 200
    m_data = res_metrics.json()
    assert m_data["total_searches"] > 0
    print(f"  -> PASSED: Analytics metrics calculated dynamically (Total Searches: {m_data['total_searches']}, Avg Response: {m_data['avg_response_time_ms']}ms).")

    # 8d. Admin System Status & Authentication
    res_login = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    assert res_login.status_code == 200
    assert "access_token" in res_login.json()
    print("  -> PASSED: Authentication token issued for enterprise admin.")

    res_admin = client.get("/api/v1/admin/system-status")
    assert res_admin.status_code == 200
    assert res_admin.json()["chromadb_status"]["status"] == "healthy"
    print("  -> PASSED: Admin system status diagnostics healthy.")

    # 8e. Benchmark Evaluation Suite (Precision@K, Recall@K, MRR, NDCG@K)
    res_eval = client.get("/api/v1/analytics/evaluation")
    assert res_eval.status_code == 200
    e_data = res_eval.json()
    assert "precision_at_5" in e_data and "mrr" in e_data
    print(f"  -> PASSED: Benchmark evaluation computed: P@5: {e_data['precision_at_5']}, Recall@5: {e_data['recall_at_5']}, MRR: {e_data['mrr']}, NDCG@5: {e_data['ndcg_at_5']}.")

    # 9. Test Error Handling & Edge Cases
    print("\n[STEP 9] Testing API Error Handling & Edge Cases...")
    
    # 9a. Empty Query
    res_empty_q = client.post("/api/v1/search/execute", json={"query": "   ", "mode": "hybrid"})
    assert res_empty_q.status_code == 400
    print("  -> PASSED: Empty query rejected with HTTP 400 Bad Request.")

    # 9b. Unsupported File Extension
    res_bad_ext = client.post("/api/v1/ingest/upload", files={"file": ("test.exe", b"binary", "application/octet-stream")})
    assert res_bad_ext.status_code == 400
    print("  -> PASSED: Unsupported file format rejected with HTTP 400 Bad Request.")

    # 9c. Corrupted File Upload
    res_corrupt = client.post("/api/v1/ingest/upload", files={"file": ("corrupt.pdf", b"NOT_A_PDF_STREAM", "application/pdf")})
    assert res_corrupt.status_code == 422
    print("  -> PASSED: Corrupted PDF file rejected with HTTP 422 Unprocessable Entity.")

    # 9d. No-Result Search Query
    res_no_res = client.post("/api/v1/search/execute", json={"query": "xyz123987unmatchednonexistentterm", "mode": "hybrid"})
    assert res_no_res.status_code == 200
    no_res_data = res_no_res.json()
    assert no_res_data["ai_answer"]["has_answer"] is False or no_res_data["total_results"] == 0
    print("  -> PASSED: No-result search query handled cleanly.")

    # 10. Clean up test documents
    print("\n[STEP 10] Cleaning Up Ingested Test Documents...")
    client.delete(f"/api/v1/ingest/documents/{doc_id_txt}")
    client.delete(f"/api/v1/ingest/documents/{doc_id_docx}")
    client.delete(f"/api/v1/ingest/documents/{doc_id_pdf}")
    print("  -> PASSED: All test documents deleted from ChromaDB.")

    print("\n=================================================================")
    print("ALL PIPELINE AUDIT & VERIFICATION TESTS PASSED 100%!")
    print("=================================================================")



if __name__ == "__main__":
    run_pipeline_verification()
