import argparse
import sys
from pathlib import Path

# Add backend directory to sys.path so app modules are resolvable
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from evaluation.config import (
    DEFAULT_DATASET_FILE,
    DEFAULT_EVAL_DOCUMENT_ID,
    TARGET_METRIC_THRESHOLDS,
)
from evaluation.evaluator import Evaluator
from evaluation.report_generator import ReportGenerator


def format_percentage(val: float) -> str:
    return f"{val * 100:.1f}%"


def print_cli_summary(eval_data: dict) -> None:
    overall = eval_data.get("overall_metrics", {})
    latency = eval_data.get("latency_summary", {})
    model = eval_data.get("model_name", "OpenRouter LLM")
    n = overall.get("total_evaluated", 0)

    print("\n" + "=" * 70)
    print(" DOCMIND AI – RAG QUALITY EVALUATION BENCHMARK SUMMARY")
    print("=" * 70)
    print(f" Model Configured: {model}")
    print(f" Evaluation Mode:  {'Mock-LLM (Zero API Cost)' if eval_data.get('mock_mode') else 'Live OpenRouter Model'}")
    print(f" Test Set Size:    {n} questions evaluated")
    print("-" * 70)
    print(f" {'METRIC':<28} | {'ACHIEVED':<12} | {'TARGET':<10} | {'STATUS':<6}")
    print("-" * 70)

    metric_rows = [
        ("Faithfulness", "faithfulness"),
        ("Context Precision", "context_precision"),
        ("Context Recall", "context_recall"),
        ("Answer Relevance", "answer_relevance"),
        ("Answer Correctness", "answer_correctness"),
        ("Citation Accuracy", "citation_accuracy"),
        ("Out-of-Syllabus Accuracy", "out_of_syllabus_accuracy"),
        ("No-Document Accuracy", "no_document_accuracy"),
    ]

    for label, key in metric_rows:
        val = overall.get(key, 0.0)
        target = TARGET_METRIC_THRESHOLDS.get(key, 0.8)
        status = "PASS" if val >= (target - 0.05) else "WARN"
        print(f" {label:<28} | {format_percentage(val):<12} | {format_percentage(target):<10} | {status:<6}")

    print("-" * 70)
    print(" LATENCY BENCHMARKS:")
    print(f"   • Mean Retrieval Latency (FAISS):   {latency.get('retrieval_mean_sec', 0):.3f}s")
    print(f"   • Mean Generation Latency (LLM):    {latency.get('generation_mean_sec', 0):.3f}s")
    print(f"   • Mean End-to-End Latency:          {latency.get('total_mean_sec', 0):.3f}s")
    print(f"   • Min / Max / P95 Latency:          {latency.get('total_min_sec', 0):.2f}s / {latency.get('total_max_sec', 0):.2f}s / {latency.get('total_p95_sec', 0):.2f}s")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="DocMind AI - Independent Model Evaluation CLI"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit evaluation to the first N questions (e.g. --limit 5 for smoke testing)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run full evaluation across all 54 questions in the benchmark dataset",
    )
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help="Filter evaluation to a specific category (e.g. conceptual_questions, comparison_questions)",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run in mock mode using ground truth as LLM answers (consumes zero OpenRouter credits)",
    )
    parser.add_argument(
        "--doc-id",
        type=str,
        default=DEFAULT_EVAL_DOCUMENT_ID,
        help=f"Target document ID in SQLite (defaults to {DEFAULT_EVAL_DOCUMENT_ID})",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=str(DEFAULT_DATASET_FILE),
        help="Path to custom evaluation dataset JSON file",
    )

    args = parser.parse_args()

    # Determine sample limit
    limit = args.limit
    if not args.full and limit is None:
        # Default to 9 questions (1 per category) if neither --full nor --limit is passed
        limit = 9

    print(f"\nInitializing DocMind AI Evaluation Engine...")
    print(f"Dataset:  {args.dataset}")
    print(f"Target:   Document ID {args.doc_id}")
    print(f"Limit:    {'All' if args.full else limit} questions")
    print(f"Mode:     {'Mock LLM (0 credits)' if args.mock else 'Live OpenRouter Inference'}\n")

    evaluator = Evaluator(
        dataset_path=args.dataset,
        target_document_id=args.doc_id,
        mock_mode=args.mock,
    )

    eval_data = evaluator.run_evaluation(
        limit=None if args.full else limit,
        category=args.category,
    )

    print("\nGenerating evaluation reports and visual charts...")
    reporter = ReportGenerator(eval_data)
    artifacts = reporter.generate_all()

    print_cli_summary(eval_data)
    print("\nArtifacts successfully written to:")
    print(f"  • JSON:   {artifacts['json']}")
    print(f"  • CSV:    {artifacts['csv']}")
    print(f"  • HTML:   {artifacts['html']}")
    for c in artifacts["charts"]:
        print(f"  • Chart:  {c}")
    print("\nOpen the HTML report in your browser to inspect visual graphs and full breakdowns.\n")


if __name__ == "__main__":
    main()
