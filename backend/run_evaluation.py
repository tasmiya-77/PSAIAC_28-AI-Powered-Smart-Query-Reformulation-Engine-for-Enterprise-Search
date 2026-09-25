import io
import docx
import pypdf
from fastapi.testclient import TestClient
from app.main import app
from app.services.evaluation import evaluation_service, BenchmarkQuery

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


def run_evaluation_benchmark():
    print("=================================================================")
    print("RUNNING STANDALONE EVALUATION & MEASUREMENT MODULE FOR AI SEARCH")
    print("=================================================================")

    # 1. Ingest test corpus
    print("\n[EVAL_SETUP] Ingesting test document corpus...")
    txt_content = b"""PostgreSQL RAG Optimization Guide:
To optimize PostgreSQL vector similarity query performance, configure HNSW index parameters (m=16, ef_construction=64).
Maintain connection pooling using asyncpg or SQLAlchemy async engine for high throughput FastAPI retrieval.
"""
    docx_content = make_docx_bytes(
        "ChromaDB Vector Store Optimization Guide",
        [
            "ChromaDB persistent client stores high-dimensional vector embeddings for fast nearest-neighbor similarity retrieval.",
            "Use BAAI/bge-small-en or Sentence Transformers for generating precise document embeddings.",
            "Reciprocal Rank Fusion (RRF) combines vector distance with BM25 lexical keyword scores."
        ]
    )
    pdf_content = make_pdf_bytes(
        "Gemini Query Reformulation Architecture",
        "Gemini 2.5 Flash reformulates raw user search queries into 5 distinct high precision candidate queries."
    )

    res_txt = client.post("/api/v1/ingest/upload", files={"file": ("eval_postgres.txt", txt_content, "text/plain")})
    res_docx = client.post("/api/v1/ingest/upload", files={"file": ("eval_chroma.docx", docx_content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})
    res_pdf = client.post("/api/v1/ingest/upload", files={"file": ("eval_gemini.pdf", pdf_content, "application/pdf")})

    doc_id_txt = res_txt.json()["document"]["document_id"]
    doc_id_docx = res_docx.json()["document"]["document_id"]
    doc_id_pdf = res_pdf.json()["document"]["document_id"]

    print("  -> Test corpus ingested successfully.")

    # 2. Define benchmark test suite with ground truth labels
    benchmark_tasks = [
        BenchmarkQuery(
            query="how to optimize postgresql vector index latency in fastapi",
            target_filenames=["eval_postgres.txt"],
            description="PostgreSQL vector latency query"
        ),
        BenchmarkQuery(
            query="chromadb vector store performance tuning best practices",
            target_filenames=["eval_chroma.docx"],
            description="ChromaDB vector store query"
        ),
        BenchmarkQuery(
            query="gemini query reformulation architecture and candidate expansion",
            target_filenames=["eval_gemini.pdf"],
            description="Gemini AI query reformulation query"
        ),
    ]

    # 3. Compute evaluation metrics
    print("\n[EVAL_BENCHMARK] Executing Search Benchmark Metrics...")
    metrics = evaluation_service.run_benchmark_eval(benchmark_tasks)

    print("\n=================================================================")
    print("MEASURED EVALUATION METRICS REPORT")
    print("=================================================================")
    print(f" Total Benchmark Queries Evaluated: {metrics.total_queries}")
    print(f" Precision@1  : {metrics.precision_at_1 * 100:.1f}%")
    print(f" Precision@3  : {metrics.precision_at_3 * 100:.1f}%")
    print(f" Precision@5  : {metrics.precision_at_5 * 100:.1f}%")
    print(f" Precision@10 : {metrics.precision_at_10 * 100:.1f}%")
    print(" ---------------------------------------------------------------")
    print(f" Recall@1     : {metrics.recall_at_1 * 100:.1f}%")
    print(f" Recall@3     : {metrics.recall_at_3 * 100:.1f}%")
    print(f" Recall@5     : {metrics.recall_at_5 * 100:.1f}%")
    print(f" Recall@10    : {metrics.recall_at_10 * 100:.1f}%")
    print(" ---------------------------------------------------------------")
    print(f" MRR (Mean Reciprocal Rank) : {metrics.mrr:.4f}")
    print(f" NDCG@5                     : {metrics.ndcg_at_5:.4f}")
    print(f" NDCG@10                    : {metrics.ndcg_at_10:.4f}")
    print(f" Average Latency            : {metrics.avg_latency_ms:.2f} ms")
    print("=================================================================")

    # 4. Clean up test documents
    print("\n[EVAL_CLEANUP] Cleaning up benchmark documents...")
    client.delete(f"/api/v1/ingest/documents/{doc_id_txt}")
    client.delete(f"/api/v1/ingest/documents/{doc_id_docx}")
    client.delete(f"/api/v1/ingest/documents/{doc_id_pdf}")
    print("  -> Cleanup complete.")
    print("=================================================================")


if __name__ == "__main__":
    run_evaluation_benchmark()
