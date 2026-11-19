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
│   │   │   ├── chat.py             # POST /api/chat (Nemotron RAG query)
│   │   │   └── sessions.py         # GET, POST, DELETE /api/sessions
│   │   └── dependencies.py         # FastAPI dependency injection providers
│   ├── core/
│   │   ├── config.py               # Centralized settings and environment variables
│   │   ├── exceptions.py           # Domain exceptions
│   │   └── logging_config.py       # Safe logging (no API keys or secrets logged)
│   ├── services/
│   │   ├── pdf_service.py          # PyPDF2 extraction with 1-indexed page tracking
│   │   ├── text_processing_service.py # Text normalization
│   │   ├── chunking_service.py     # LangChain RecursiveCharacterTextSplitter
│   │   ├── embedding_service.py    # Local Sentence Transformers singleton
│   │   ├── vector_store_service.py # LangChain FAISS persistence & deletion
│   │   ├── retrieval_service.py    # Semantic search & relevance score filtering
│   │   ├── llm_service.py          # OpenRouter Nemotron integration & system prompt
│   │   ├── citation_service.py     # Verified citation builder from retrieved chunks
│   │   └── chat_service.py         # End-to-end RAG orchestrator & message persistence
│   ├── models/
│   │   ├── document.py             # Document & index metadata dataclasses
│   │   ├── chat.py                 # Message & citation dataclasses
│   │   └── session.py              # Session dataclass
│   ├── schemas/
│   │   ├── document_schema.py      # Pydantic document request/response models
│   │   ├── chat_schema.py          # Pydantic chat request/response models
│   │   └── session_schema.py       # Pydantic session request/response models
│   ├── database/
│   │   ├── connection.py           # Thread-safe SQLite connection context
│   │   ├── initialization.py       # Table creation & indexes
│   │   └── repository.py           # CRUD repository methods
│   └── utils/
│       ├── file_validator.py       # Magic byte %PDF- and size validation
│       └── text_cleaner.py         # Whitespace and prompt-injection sanitization
├── storage/
│   ├── uploads/                    # Physical PDF documents
│   ├── indexes/                    # FAISS vector indexes (isolated per document)
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
