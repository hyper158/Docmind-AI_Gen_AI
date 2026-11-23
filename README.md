# DocMind AI – Ask the Syllabus Bot

DocMind AI is an intelligent, document-grounded study assistant application. It allows students and researchers to upload syllabi, course textbooks, lecture notes, and research papers, indexing them with local vector embeddings and answering questions using NVIDIA Nemotron 3.5 Lightning via OpenRouter with verified page citations.

---

## 🏛 Project Directory Structure

```
DocMind-AI/
│
├── frontend/                       # React 19 + TypeScript + Vite + Tailwind CSS
│   ├── src/
│   │   ├── components/             # Reusable UI components (ChatInput, Header, FileUploadModal, etc.)
│   │   ├── pages/                  # ChatPage, DocumentsPage, AnalyticsPage
│   │   ├── services/               # Centralized api.ts communicating with backend
│   │   ├── types/                  # TypeScript interface definitions
│   │   └── App.tsx                 # Root layout and session state manager
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── backend/                        # Python FastAPI RAG Service
│   ├── app/
│   │   ├── main.py                 # FastAPI application entrypoint
│   │   ├── api/routes/             # Health, Documents, Chat, Sessions endpoints
│   │   ├── core/                   # Config, logging, domain exceptions
│   │   ├── services/               # PDF, chunking, embeddings, FAISS, Nemotron, citations
│   │   ├── models/                 # SQLite dataclasses
│   │   ├── schemas/                # Pydantic request/response validation schemas
│   │   ├── database/               # SQLite connection, tables, repository
│   │   └── utils/                  # File validation and text cleaning
│   ├── storage/
│   │   ├── uploads/                # Stored PDF documents
│   │   ├── indexes/                # Persistent FAISS vector indexes
│   │   └── metadata/               # SQLite database file (docmind.db)
│   ├── tests/                      # Pytest automated test suite
│   ├── requirements.txt
│   ├── .env.example
│   ├── .gitignore
│   └── README.md
│
├── README.md                       # Master project overview & execution guide
└── .gitignore                      # Root gitignore
```

---

## 🚀 Quick Start Guide (Windows PowerShell)

Follow these steps to run both the backend and frontend simultaneously.

### Step 1: Start the Backend (Terminal 1)

1. Open a PowerShell terminal and navigate to the `backend` folder:
   ```powershell
   cd backend
   ```

2. Activate the virtual environment (created during setup):
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

3. Ensure dependencies are installed:
   ```powershell
   pip install -r requirements.txt
   ```

4. Configure your `.env` file (copy from `.env.example` if not already present):
   ```powershell
   Copy-Item .env.example .env
   ```
   Add your OpenRouter API key in `.env`:
   ```env
   OPENROUTER_API_KEY=sk-or-v1-your-key-here
   OPENROUTER_MODEL=nvidia/nemotron-3.5-lightning:free
   ```

5. Start the FastAPI backend server:
   ```powershell
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   - Swagger Documentation: `http://localhost:8000/docs`
   - Health Check: `http://localhost:8000/api/health`

---

### Step 2: Start the Frontend (Terminal 2)

1. Open a second PowerShell terminal and navigate to the `frontend` folder:
   ```powershell
   cd frontend
   ```

2. Install npm dependencies:
   ```powershell
   npm install
   ```

3. Start the Vite development server:
   ```powershell
   npm run dev
   ```

4. Open your browser and navigate to:
   ```
   http://localhost:5173
   ```

---

## 🧪 Running Automated Tests

Run the backend Pytest suite (mocks the LLM and runs completely offline, consuming 0 API credits):

```powershell
cd backend
.\venv\Scripts\Activate.ps1
pytest -v
```

---

## 📊 Independent Model Evaluation System

DocMind AI includes an automated benchmark and evaluation engine located in `backend/evaluation/`. It assesses the RAG pipeline across 9 question categories (Direct, Conceptual, Comparison, Application, Scenario, Summarization, Explanation, Multi-part, and Out-of-Syllabus/No-Doc) and produces multi-format reports and Matplotlib charts in `backend/evaluation_results/`.

### Run Mock Evaluation (Fast, Zero OpenRouter API Cost)
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m evaluation.evaluate --mock --full
```

### Run Live Model Evaluation
```powershell
# Smoke test (5 questions)
python -m evaluation.evaluate --limit 5

# Full live benchmark (all 54 curated questions)
python -m evaluation.evaluate --full
```

### View Evaluation Report & Charts
Open the generated visual report in your browser:
```powershell
Start-Process "evaluation_results\evaluation_report.html"
```

Generated artifacts in `backend/evaluation_results/`:
- `metrics.json` – Machine-readable evaluation KPI scores
- `test_results.csv` – Execution trace for each benchmark question
- `evaluation_report.html` – Interactive visual dashboard with KPI cards and sample inspector
- `charts/` – Matplotlib visualizations (`overall_metrics.png`, `category_performance.png`, `latency_breakdown.png`)

---

## 📖 End-to-End User Workflow

1. **Upload Syllabus**: Click the **Upload New File** button in the header or welcome screen and drop a PDF file.
2. **Extraction & Indexing**: The backend uses PyPDF2 to extract text page-by-page, converts pages into LangChain Document objects with 1-indexed page metadata, creates 512-character chunks with 64-character overlap, generates local FastEmbed ONNX embeddings (`BAAI/bge-small-en-v1.5`), and indexes them in a local FAISS vector store.
3. **No-PDF Check**: If you ask a question without uploading a syllabus PDF, the system strictly returns: `"I cannot answer because no syllabus PDF has been uploaded. Please upload your study material first."` without invoking the LLM or fabricating citations.
4. **Ask a Question**: Type direct, conceptual, comparison, application, scenario, summarization, or multi-part questions.
5. **Grounded Answer & Citations**: The backend performs Top-K semantic retrieval from FAISS, filters by relevance score, builds a bounded context, queries NVIDIA Nemotron 3.5 Lightning via OpenRouter, and presents the answer directly into the chat UI formatted in Markdown along with verified citations indicating the exact PDF filename and page number.
6. **Document Viewer**: Click any citation badge to open the side drawer and inspect the referenced excerpt.
7. **Hierarchical Document Summarizer**: Navigate to the Documents page and click "Summarize" on any document. The backend runs a page-aware Map-Reduce pipeline that produces an 8-section comprehensive synthesis, individual page-by-page summaries, and extraction diagnostics with live progress tracking.
8. **Session Persistence**: Sessions, chat history, and uploaded documents persist across application restarts in SQLite and local disk storage.
