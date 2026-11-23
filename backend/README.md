# DocMind AI – Python RAG Backend

DocMind AI is a factual, document-grounded syllabus assistant. It allows students to upload PDFs (syllabi, course notes, research papers), extracts and chunks text using PyPDF2 and LangChain, creates local embeddings with `sentence-transformers/all-MiniLM-L6-v2`, indexes them in a persistent FAISS vector store, and generates answers using NVIDIA Nemotron 3.5 Lightning via OpenRouter with verified source citations.

---

## 🛠 Technology Stack

- **Framework**: Python 3.10+ / FastAPI / Uvicorn
- **PDF Extraction**: PyPDF2
- **Document Model & Chunking**: LangChain Core / LangChain Text Splitters
- **Embeddings**: FastEmbed (`BAAI/bge-small-en-v1.5`, ONNX Runtime, 384 dimensions, CPU-only, PyTorch-free)
- **Vector Store**: FAISS (`langchain-community` / `faiss-cpu`)
- **LLM**: NVIDIA Nemotron 3.5 Lightning (`nvidia/nemotron-3.5-lightning:free`) via OpenRouter (`langchain-openai`)
- **Database**: SQLite (WAL mode, foreign keys enabled)
- **Evaluation & Benchmarking**: Standalone evaluation module (`backend/evaluation/`) with Matplotlib chart generation
- **Validation**: Pydantic v2 / Pydantic Settings
- **Testing**: Pytest / Pytest-Asyncio / HTTPX TestClient

---

## 📂 Architecture & Directory Layout

```
backend/
├── app/
│   ├── main.py                     # FastAPI application entrypoint & middleware
│   ├── api/
│   │   ├── routes/
│   │   │   ├── health.py           # GET /api/health
│   │   │   ├── documents.py        # POST /api/documents/upload, GET, DELETE
│   │   │   ├── summarization.py    # POST /api/documents/{id}/summarize, GET status/summary
│   │   │   ├── chat.py             # POST /api/chat (Nemotron RAG query)
│   │   │   ├── sessions.py         # GET, POST, DELETE /api/sessions
│   │   │   └── evaluation.py       # GET/POST /api/evaluation/* (RAG evaluation metrics)
│   │   └── dependencies.py         # FastAPI dependency injection providers
│   ├── core/
│   │   ├── config.py               # Centralized settings and environment variables
│   │   ├── exceptions.py           # Domain exceptions
│   │   └── logging_config.py       # Safe logging (no API keys or secrets logged)
│   ├── services/
│   │   ├── pdf_service.py          # PyPDF2 extraction with 1-indexed page tracking & diagnostics
│   │   ├── summarization/          # Hierarchical Map-Reduce PDF Summarization Engine
│   │   │   ├── token_budget.py     # Sub-chunking, sentence boundary split & token estimator
│   │   │   ├── prompt_templates.py # Page, sub-chunk, section merge & master synthesis prompts
│   │   │   ├── page_summarizer.py  # Semaphore-bounded per-page summarization with retries
│   │   │   ├── hierarchical_aggregator.py # Multi-level hierarchical section reduction
│   │   │   └── summarization_service.py   # Pipeline orchestrator with progress & dual persistence
│   │   ├── text_processing_service.py # Text normalization
│   │   ├── chunking_service.py     # LangChain RecursiveCharacterTextSplitter
│   │   ├── embedding_service.py    # Local Sentence Transformers singleton
│   │   ├── vector_store_service.py # LangChain FAISS persistence & deletion
│   │   ├── retrieval_service.py    # Semantic search & relevance score filtering
│   │   ├── llm_service.py          # OpenRouter Nemotron integration & system prompt
│   │   ├── citation_service.py     # Verified citation builder from retrieved chunks
│   │   └── chat_service.py         # End-to-end RAG orchestrator with summary context injection
│   ├── models/
│   │   ├── document.py             # Document & index metadata dataclasses
│   │   ├── chat.py                 # Message & citation dataclasses
│   │   └── session.py              # Session dataclass
│   ├── schemas/
│   │   ├── document_schema.py      # Pydantic document request/response models
│   │   ├── summarization_schema.py # Pydantic hierarchical summarization models
│   │   ├── chat_schema.py          # Pydantic chat request/response models
│   │   └── session_schema.py       # Pydantic session request/response models
│   ├── database/
│   │   ├── connection.py           # Thread-safe SQLite connection context
│   │   ├── initialization.py       # Table creation (documents, chunks, sessions, document_summaries)
│   │   └── repository.py           # CRUD repository methods
│   └── utils/
│       ├── file_validator.py       # Magic byte %PDF- and size validation
│       └── text_cleaner.py         # Whitespace and prompt-injection sanitization
├── evaluation/                     # Standalone evaluation & benchmark engine
├── storage/
│   ├── uploads/                    # Physical PDF documents
│   ├── indexes/                    # FAISS vector indexes (isolated per document)
│   ├── summaries/                  # Master JSON summaries cache
│   └── metadata/                   # SQLite database (docmind.db)
├── tests/                          # Automated Pytest suite
├── requirements.txt                # Pinned dependencies
├── .env.example                    # Environment variable template
├── .gitignore
└── README.md
```

---

## 🧠 LangChain RAG Pipeline

```
PDF File Upload
       ↓
PyPDF2 Page-by-Page Extraction
       ↓
Text Normalization & Injection Neutralization
       ↓
LangChain RecursiveCharacterTextSplitter (chunk_size=512, overlap=64)
       ↓
Local Sentence Transformers Embeddings (all-MiniLM-L6-v2)
       ↓
FAISS Vector Store Indexing (storage/indexes/{document_id}/)
       ↓
Student Question -> Local Embedding Query
       ↓
FAISS Top-K Semantic Retrieval (Cosine similarity normalized)
       ↓
Relevance Score Filtering (Threshold >= 0.35)
       ↓
Bounded Study Context Construction
       ↓
NVIDIA Nemotron 3.5 Lightning (via OpenRouter ChatOpenAI)
       ↓
Strict Citation Verification (Page & snippet match)
       ↓
Structured JSON Response + SQLite Persistence
```

---

## 📑 Hierarchical PDF Summarization Pipeline (Map-Reduce)

```
PDF Document (1 to 100+ Pages)
       ↓
[Stage 1: Complete PDF Extraction]
PyPDF2 Page-by-Page Extraction -> Extraction Diagnostics Report (Total, Empty, Insufficient, Failed)
       ↓
[Stage 2: Intelligent Page-Level Summarization (MAP)]
Dense Pages (>3000 chars) -> Sentence-Boundary Sub-Chunking (chunk_size=3000, overlap=300)
Sub-Chunk Summaries -> Merged Page Summary
Bounded Concurrency Semaphore (concurrency=3) + Exponential Backoff Retries
Output: 1 Structured Page Summary per page with bullet points and key terms
       ↓
[Stage 3: Hierarchical Multi-Level Aggregation (REDUCE)]
Group Consecutive Page Summaries into Batches of 5 -> Level-1 Section Summaries
(Recursive reduction if Level-1 exceeds 6000 tokens)
       ↓
[Stage 4: Master Document Synthesis]
8-Section Comprehensive Architecture:
1. Executive Overview & Document Purpose
2. Core Themes & Structural Breakdown
3. In-Depth Chapter / Concept Analysis
4. Terminology & Key Definitions
5. Methodologies, Frameworks & Processes
6. Quantitative Details, Formulas & Policies
7. Major Takeaways, Conclusions & Actionable Items
8. Document Coverage & Page Citation Matrix
       ↓
[Dual Persistence & Chat Injection]
- SQLite Database: `document_summaries` table
- File Cache: `storage/summaries/{document_id}.json`
- Grounding: Automatically injected into chat context for full-document summary queries
```

---

## ⚡ Setup & Execution Instructions (Windows PowerShell)

### 1. Create and Activate Virtual Environment

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and set your OpenRouter API key:

```env
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
OPENROUTER_MODEL=nvidia/nemotron-3.5-lightning:free
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MAX_TOKENS=512
OPENROUTER_TEMPERATURE=0.1
```

### 4. Run Automated Tests

The automated test suite mocks the LLM and runs completely offline, consuming **0 OpenRouter credits**:

```powershell
pytest
```

### 5. Start the FastAPI Backend Server

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The interactive Swagger API documentation will be available at:
`http://localhost:8000/docs`

---

## 📡 API Endpoints Reference

### Health
- `GET /api/health`: Returns service health status, model, and embedding configuration.

### Documents
- `POST /api/documents/upload`: Uploads a PDF file (`multipart/form-data`), validates format/magic bytes, extracts text with PyPDF2, splits into LangChain chunks, embeds with MiniLM, and indexes in FAISS.
- `GET /api/documents`: Lists all uploaded documents with page count, chunk count, file size, and processing status.
- `GET /api/documents/{document_id}`: Retrieves details for a specific document.
- `DELETE /api/documents/{document_id}`: Deletes the physical PDF, deletes the FAISS index files, and removes all associated metadata.

### Hierarchical PDF Summarization
- `POST /api/documents/{document_id}/summarize`: Triggers hierarchical Map-Reduce summarization.
  - Optional JSON body: `{"run_in_background": true, "force_regenerate": false}`
  - Returns `200 OK` (synchronous) or `202 Accepted` with `job_id` (asynchronous).
- `GET /api/documents/{document_id}/summary`: Retrieves the comprehensive document summary including the 8-section master synthesis, individual page summaries, and extraction diagnostics report.
- `GET /api/documents/{document_id}/summary/status`: Lightweight polling endpoint returning status (`not_started`, `extracting`, `summarizing_pages`, `aggregating`, `completed`, `failed`), progress percentage, and processed page counts.

### Chat Q&A
- `POST /api/chat`:
  - **Request Body**:
    ```json
    {
      "question": "What are the grading criteria in the syllabus?",
      "session_id": "session_optional",
      "selected_document_ids": ["doc_abc123"]
    }
    ```
  - **Response Body**:
    ```json
    {
      "answer": "According to page 3 of the syllabus, the grading criteria consists of 40% midterms...",
      "session_id": "session_abc",
      "message_id": "msg_xyz",
      "citations": [
        {
          "citation_id": "cit_1",
          "document_id": "doc_abc123",
          "filename": "CS101_Syllabus.pdf",
          "page_number": 3,
          "chunk_id": "doc_abc123_p3_c1",
          "relevant_text_snippet": "Grading Policy: Midterm Exam 40%, Final Exam 40%, Homework 20%.",
          "relevance_score": 0.892
        }
      ],
      "answer_status": "grounded",
      "retrieved_source_count": 3,
      "thinking_process": "Searched FAISS index across 1 document. Retrieved 3 relevant chunks...",
      "reasoning_time": 1.42
    }
    ```

### Sessions
- `GET /api/sessions`: Returns all chat sessions.
- `POST /api/sessions`: Creates a new session.
- `GET /api/sessions/{session_id}`: Returns complete chat history, linked documents, and message citations.
- `DELETE /api/sessions/{session_id}`: Deletes a session and its message history.

---

## 🛡 Security & Credit Optimization

1. **Local Embeddings**: Embeddings run entirely on your CPU via HuggingFace Sentence Transformers. OpenRouter credits are **never** used for embeddings or indexing.
2. **Deterministic Citations**: Citations are derived exclusively from the retrieved LangChain Document chunks. No secondary LLM calls are made for verification.
3. **Prompt Injection Protection**: Document text is sanitized before being inserted into prompt templates.
4. **Offline Test Suite**: Tests use mocked responses to guarantee that running `pytest` never incurs API charges.
