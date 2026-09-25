# AI-Powered Smart Query Reformulation & Enterprise Search Engine

An enterprise-grade, high-performance RAG and query reformulation platform built with **Next.js 15 (App Router, TypeScript)**, **Tailwind CSS**, **FastAPI (Python 3.12)**, **ChromaDB Vector Store**, **Sentence Transformers**, and **Google Gemini 2.5 AI**.

---

## 🚀 Key Features

1. **Document Ingestion & Indexing Pipeline**:
   - Multi-format ingestion: **PDF**, **DOCX**, **TXT**, and **MD** parsing.
   - SHA-256 duplicate content hash prevention to avoid redundant indexing.
   - Sliding overlap chunking (`chunk_size=500`, `chunk_overlap=50`).
   - High-performance vector embeddings via `SentenceTransformerEmbeddingFunction` (`BAAI/bge-small-en-v1.5` / `all-MiniLM-L6-v2`) in ChromaDB.

2. **Query Reformulation & Expansion**:
   - Powered by **Google Gemini 2.5 Flash** (`google-genai` SDK).
   - Extracts intent (`TROUBLESHOOTING`, `TECHNICAL_SEARCH`, `CONCEPTUAL_EXPLANATION`) and domain entities.
   - Expands raw queries into 5 candidate reformulations with strategy scoring.

3. **Dual-Path Hybrid Retrieval & BGE Reranking**:
   - **BM25 Lexical Keyword Search** + **ChromaDB Dense Vector Search**.
   - Reciprocal Rank Fusion (RRF) candidate deduplication and retrieval (Top 50).
   - **BGE Cross-Encoder Reranking** (`BAAI/bge-reranker-base`) evaluating query-passage pairs to output the Top 10 results with exact confidence levels.

4. **Transparent Explainable Search ("Why this result?")**:
   - Interactive UI disclosure accordion rendering:
     - Score breakdown: `Semantic Score`, `BM25 Score`, `BGE Rerank Score`, `Final Relevance`.
     - Retrieval path identifier (`Hybrid BM25 + ChromaDB Vector`).
     - Selection rationale matching intent and entity alignment.

5. **User Feedback Layer & Satisfaction Telemetry**:
   - Inline 👍 Helpful / 👎 Not Helpful rating buttons with optional comment text submission.
   - Thread-safe persistence storing feedback metadata (`query`, `reformulated_query`, `document_id`, `rating`, `timestamp`).
   - Analytics dashboard displaying **Helpful Rate (%)**, **Not-Helpful Rate (%)**, **Most Useful Documents**, and **Query Success Rankings**.

6. **Information Retrieval (IR) Evaluation Engine**:
   - Standalone evaluation module measuring:
     - **Precision@K** ($K=1, 3, 5, 10$)
     - **Recall@K** ($K=1, 3, 5, 10$)
     - **MRR** (Mean Reciprocal Rank)
     - **NDCG@K** (Normalized Discounted Cumulative Gain at $K=5, 10$)
     - **Average Response Latency** (ms)

---

## 🛠️ Tech Stack & Technologies Used

- **Frontend**: Next.js 15 (App Router, React 19, TypeScript), Tailwind CSS, Lucide Icons, Framer Motion.
- **Backend**: FastAPI (Python 3.12), Pydantic v2, Uvicorn.
- **Vector Database**: ChromaDB (Persistent client storage).
- **AI & Embedding Models**:
  - `google-genai` (Gemini 2.5 Flash)
  - `sentence-transformers` (`BAAI/bge-small-en-v1.5`)
  - `transformers` (`BAAI/bge-reranker-base`)
- **Document Extractors**: `pypdf`, `python-docx`.

---

## 📦 Environment Variables Configuration

Create a `.env` file in the root or `backend/` directory based on `.env.example`:

```env
# AI Backend Environment Configuration
ENVIRONMENT=development
PROJECT_NAME="AI-Powered Smart Query Reformulation Engine"
VERSION=1.0.0

# Google Gemini AI Credentials
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Vector Store & Embedding Configuration
CHROMADB_STORAGE_PATH=./data/chromadb
CHROMADB_COLLECTION_NAME=enterprise_knowledge_base
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5
EMBEDDING_DIMENSION=384

# Frontend Environment Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

---

## 💻 Quick Start Guide

### Prerequisites
- Python 3.12+
- Node.js 20+

### 1. Setup Backend (FastAPI)
```bash
cd backend
python -m venv venv

# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Interactive API Documentation: `http://localhost:8000/api/v1/docs`

### 2. Setup Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```
Open application in browser: `http://localhost:3000`

---

## 🐳 Running with Docker & Docker Compose

```bash
# Copy environment template
cp .env.example .env

# Build and spin up containers
docker-compose up --build
```
- Frontend UI: `http://localhost:3000`
- Backend API: `http://localhost:8000`

---

## 🧪 Testing & Validation

### Run Complete End-to-End Pipeline Verification Suite
```bash
cd backend
venv\Scripts\python.exe test_pipeline_verification.py
```

### Run User Feedback Layer Test Suite
```bash
cd backend
venv\Scripts\python.exe test_feedback_layer.py
```

### Run Standalone IR Evaluation Engine Benchmark
```bash
cd backend
venv\Scripts\python.exe run_evaluation.py
```

### Verify Frontend TypeScript Build
```bash
cd frontend
npm run build
```

---

## 📊 End-to-End System Workflow

```
User Document Upload (PDF, DOCX, TXT)
 └─► SHA-256 Duplicate Check & Extraction
      └─► Chunking & Sentence Transformers Embedding
           └─► Indexing in ChromaDB Persistent Collection
                └─► User Query Input
                     └─► Gemini 2.5 Flash Query Reformulation & Intent Extraction
                          └─► BM25 Keyword + Vector Distance Dual-Path Retrieval
                               └─► BGE Cross-Encoder Reranking
                                    └─► Top Results with "Why this result?" Explainability
                                         └─► User 👍/👎 Feedback & Comments
                                              └─► Real-Time Analytics & IR Metrics
```
