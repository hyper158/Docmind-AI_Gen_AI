from pathlib import Path
from typing import Dict, Any

EVALUATION_DIR = Path(__file__).resolve().parent
BACKEND_DIR = EVALUATION_DIR.parent
RESULTS_DIR = BACKEND_DIR / "evaluation_results"
CHARTS_DIR = RESULTS_DIR / "charts"
DATASETS_DIR = EVALUATION_DIR / "datasets"

DEFAULT_DATASET_FILE = DATASETS_DIR / "evaluation_dataset.json"
DEFAULT_EVAL_DOCUMENT_ID = "doc_5593b687be94"
DEFAULT_EVAL_DOCUMENT_NAME = "Machine_Learning_&_Deep_Learning__Comprehensive_Technical_Terminology_Compendium.pdf"

# Metric Threshold Targets for acceptable RAG performance
TARGET_METRIC_THRESHOLDS: Dict[str, float] = {
    "faithfulness": 0.85,
    "context_precision": 0.80,
    "context_recall": 0.80,
    "answer_relevance": 0.75,
    "citation_accuracy": 0.90,
    "out_of_syllabus_accuracy": 0.95,
    "no_document_accuracy": 1.00,
}

# Ensure result and chart directories exist
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
CHARTS_DIR.mkdir(parents=True, exist_ok=True)
DATASETS_DIR.mkdir(parents=True, exist_ok=True)
