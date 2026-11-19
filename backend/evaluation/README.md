# DocMind AI – Independent Model Evaluation System

This directory houses the independent evaluation framework for the **DocMind AI – Syllabus Question Answering System**. It provides automated, objective benchmarking of the retrieval-augmented generation (RAG) pipeline across 9 distinct question styles without touching the frontend user interface.

---

## 1. Evaluation Architecture

```
backend/
├── evaluation/
│   ├── datasets/
│   │   └── evaluation_dataset.json   # 54 curated test cases across 9 categories
│   ├── config.py                     # Evaluation paths, thresholds, and target IDs
│   ├── metrics.py                    # Mathematical formulations for RAG quality metrics
│   ├── evaluator.py                  # Evaluation loop, latency timer, and scoring
│   ├── report_generator.py           # Multi-format artifact generator (JSON, CSV, PNG, HTML)
│   ├── evaluate.py                   # Standalone CLI entry point
│   └── README.md                     # This documentation
│
└── evaluation_results/
    ├── metrics.json                  # Aggregate and per-category metric summary
    ├── test_results.csv              # Per-question test execution records
    ├── evaluation_report.html        # Interactive, dark-mode visual HTML report
    └── charts/
        ├── overall_metrics.png       # Core metrics vs target thresholds
        ├── category_performance.png  # Performance across all 9 question categories
        └── latency_breakdown.png     # FAISS retrieval vs LLM generation latency
```

---

## 2. Curated Evaluation Dataset

The benchmark dataset in `datasets/evaluation_dataset.json` contains 54 high-quality test cases based on the syllabus document `Machine_Learning_&_Deep_Learning__Comprehensive_Technical_Terminology_Compendium.pdf` (`doc_5593b687be94`), spanning 9 distinct categories:

| Category | Count | Focus |
| :--- | :---: | :--- |
| **Direct Questions** | 6 | Accurate definitions, mathematical formulas, and explicit facts |
| **Conceptual Questions** | 6 | Understanding principles (e.g. why attention replaces recurrence) |
| **Comparison Questions** | 6 | Contrasting models/techniques (e.g. BERT vs GPT, L1 vs L2) |
| **Application Questions** | 6 | Concrete usage in workflows (e.g. LoRA parameter adaptation) |
| **Scenario Questions** | 6 | Failure modes and edge conditions (e.g. vanishing gradients) |
| **Summarization Questions**| 6 | Multi-concept synthesis across syllabus volumes |
| **Explanation Questions** | 6 | Plain language step-by-step mechanisms (e.g. diffusion reverse) |
| **Multi-Part Questions** | 6 | Complex compound queries with partial context handling |
| **Out-of-Syllabus / Edge** | 6 | Rejection of out-of-scope topics and no-document enforcement |

---

## 3. Evaluated Metrics & Formulations

1. **Faithfulness / Groundedness ($\ge 85\%$)**:
   $$\text{Faithfulness} = \frac{\text{Count of Claims Supported by Context}}{\text{Total Claims in Answer}}$$
   Prevents external hallucinations by verifying that statements in the answer are grounded in retrieved excerpts.

2. **Context Precision ($\ge 80\%$)**:
   $$\text{Context Precision} = \frac{\text{Relevant Retrieved Chunks}}{\text{Total Retrieved Chunks}}$$
   Measures FAISS retrieval signal-to-noise ratio against ground-truth pages and key terms.

3. **Context Recall ($\ge 80\%$)**:
   $$\text{Context Recall} = 0.5 \times \text{Page Recall} + 0.5 \times \text{Key Term Recall}$$
   Verifies that the retrieved passages capture all necessary ground-truth concepts.

4. **Answer Relevance ($\ge 75\%$)**:
   Measures lexical and semantic token alignment ($F_1$ harmonic mean) between student questions and generated responses.

5. **Answer Correctness ($\ge 80\%$)**:
   Compares the factual substance of generated responses against verified ground-truth answers.

6. **Citation Accuracy ($\ge 90\%$)**:
   Validates that generated citations point to valid syllabus page numbers and contain authentic text snippets.

7. **Out-of-Syllabus Detection ($\ge 95\%$)**:
   Ensures out-of-scope questions receive the exact mandated refusal without hallucinated citations.

8. **No-Document Handling ($100\%$)**:
   Validates that asking a question when zero syllabus PDFs are uploaded returns the exact string:
   `"I cannot answer because no syllabus PDF has been uploaded. Please upload your study material first."` with zero citations.

9. **Latency Profile**:
   Measures retrieval latency, LLM inference latency, and total end-to-end latency (Mean, Min, Max, P50, P95).

---

## 4. How to Run Evaluation

Navigate to the `backend/` directory in PowerShell and activate the virtual environment:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
```

### A. Mock Evaluation (Fast, Zero OpenRouter API Cost)
Runs the entire pipeline using ground-truth responses as the LLM generation, scoring FAISS retrieval, context precision, recall, citation verification, and chart creation without consuming API credits:

```powershell
python -m evaluation.evaluate --mock --full
```

Quick smoke test (first 5 samples):
```powershell
python -m evaluation.evaluate --mock --limit 5
```

### B. Live OpenRouter LLM Evaluation
Runs live inference using the configured model (`nvidia/nemotron-3.5-lightning:free`):

```powershell
python -m evaluation.evaluate --limit 5
```

Full live benchmark across all 54 questions:
```powershell
python -m evaluation.evaluate --full
```

### C. Evaluate a Specific Category
Filter execution to a single question style:
```powershell
python -m evaluation.evaluate --mock --category comparison_questions
```

---

## 5. Viewing Evaluation Reports

After running the evaluation, open the self-contained HTML report in your browser:

```powershell
# In PowerShell:
Start-Process "evaluation_results\evaluation_report.html"
```

The report includes:
- **KPI Summary Cards**: Overall Faithfulness, Precision, Recall, and Citation Accuracy.
- **Embedded Visual Charts**: Overall metrics, category breakdown, and latency bars.
- **Category Performance Table**: Breakdown by question style.
- **Collapsible Test Sample Explorer**: Click any test case to inspect the user question, ground truth, generated answer, cited pages, and metric scores.
