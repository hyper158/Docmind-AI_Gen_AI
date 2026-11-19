import json
import time
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.services.chat_service import ChatService
from app.services.retrieval_service import RetrievalService
from evaluation.config import (
    DEFAULT_DATASET_FILE,
    DEFAULT_EVAL_DOCUMENT_ID,
    TARGET_METRIC_THRESHOLDS,
)
from evaluation.metrics import (
    compute_context_precision,
    compute_context_recall,
    compute_faithfulness,
    compute_answer_relevance,
    compute_answer_correctness,
    compute_citation_accuracy,
    compute_out_of_syllabus_accuracy,
    compute_no_document_accuracy,
)


class Evaluator:
    """Orchestrates end-to-end evaluation of the DocMind RAG pipeline."""

    def __init__(
        self,
        dataset_path: Optional[str] = None,
        target_document_id: str = DEFAULT_EVAL_DOCUMENT_ID,
        mock_mode: bool = False,
    ) -> None:
        self.dataset_path = dataset_path or str(DEFAULT_DATASET_FILE)
        self.target_document_id = target_document_id
        self.mock_mode = mock_mode
        self.chat_service = ChatService()
        self.retrieval_service = RetrievalService()

    def load_dataset(self) -> List[Dict[str, Any]]:
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def evaluate_sample(
        self,
        item: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Runs a single test case through RAG pipeline and scores metrics."""
        question = item["question"]
        gt_answer = item["ground_truth_answer"]
        gt_pages = item.get("ground_truth_pages", [])
        key_terms = item.get("key_terms", [])
        is_oos = item.get("is_out_of_syllabus", False)
        is_nodoc = item.get("is_no_document", False)

        doc_ids = [] if is_nodoc else [self.target_document_id]

        # 1. Measure Retrieval Stage
        t_ret_start = time.perf_counter()
        if doc_ids:
            retrieved_chunks = self.retrieval_service.retrieve_chunks(
                query=question,
                document_ids=doc_ids,
            )
        else:
            retrieved_chunks = []
        retrieval_latency = round(time.perf_counter() - t_ret_start, 3)

        # 2. Execute Chat Pipeline
        t_tot_start = time.perf_counter()
        mock_resp = gt_answer if self.mock_mode else None

        response = self.chat_service.process_chat(
            question=question,
            selected_document_ids=doc_ids,
            mock_llm_response=mock_resp,
        )
        total_latency = round(time.perf_counter() - t_tot_start, 3)
        if response.reasoning_time is not None and response.reasoning_time > 0:
            gen_latency = round(response.reasoning_time, 3)
        else:
            gen_latency = max(0.01, round(total_latency, 3))

        answer = response.answer
        citations = response.citations
        answer_status = response.answer_status

        # 3. Calculate Transparent Metrics
        ctx_prec = compute_context_precision(retrieved_chunks, gt_pages, key_terms)
        ctx_rec = compute_context_recall(retrieved_chunks, gt_pages, key_terms)
        faith = compute_faithfulness(answer, retrieved_chunks, answer_status)
        relevance = compute_answer_relevance(question, answer)
        correctness = compute_answer_correctness(answer, gt_answer)
        cit_acc = compute_citation_accuracy(citations, gt_pages, is_oos, is_nodoc)
        oos_acc = compute_out_of_syllabus_accuracy(answer, answer_status, is_oos)
        nodoc_acc = compute_no_document_accuracy(answer, citations, answer_status, is_nodoc)

        return {
            "id": item["id"],
            "category": item["category"],
            "question": question,
            "ground_truth_answer": gt_answer,
            "generated_answer": answer,
            "answer_status": answer_status,
            "retrieved_chunk_count": len(retrieved_chunks),
            "citation_count": len(citations),
            "citations": [c.model_dump() if hasattr(c, "model_dump") else str(c) for c in citations],
            "retrieval_latency_sec": retrieval_latency,
            "generation_latency_sec": gen_latency,
            "total_latency_sec": total_latency,
            "context_precision": ctx_prec,
            "context_recall": ctx_rec,
            "faithfulness": faith,
            "answer_relevance": relevance,
            "answer_correctness": correctness,
            "citation_accuracy": cit_acc,
            "out_of_syllabus_accuracy": oos_acc,
            "no_document_accuracy": nodoc_acc,
        }

    def run_evaluation(
        self,
        limit: Optional[int] = None,
        category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Runs evaluation over the dataset and aggregates results."""
        dataset = self.load_dataset()
        if category:
            dataset = [d for d in dataset if d["category"] == category]
        if limit and limit > 0:
            dataset = dataset[:limit]

        results = []
        for idx, item in enumerate(dataset):
            print(f"[{idx + 1}/{len(dataset)}] Evaluating ({item['category']}): {item['question'][:60]}...")
            sample_result = self.evaluate_sample(item)
            results.append(sample_result)

        # Aggregate Metrics
        n = len(results)
        if n == 0:
            return {"total_tests": 0, "results": []}

        def _mean(key: str) -> float:
            return round(sum(r[key] for r in results) / n, 4)

        overall_metrics = {
            "total_evaluated": n,
            "faithfulness": _mean("faithfulness"),
            "context_precision": _mean("context_precision"),
            "context_recall": _mean("context_recall"),
            "answer_relevance": _mean("answer_relevance"),
            "answer_correctness": _mean("answer_correctness"),
            "citation_accuracy": _mean("citation_accuracy"),
            "out_of_syllabus_accuracy": _mean("out_of_syllabus_accuracy"),
            "no_document_accuracy": _mean("no_document_accuracy"),
        }

        # Latencies
        ret_lats = [r["retrieval_latency_sec"] for r in results]
        gen_lats = [r["generation_latency_sec"] for r in results]
        tot_lats = [r["total_latency_sec"] for r in results]

        tot_lats_sorted = sorted(tot_lats)
        p50_idx = int(0.50 * n)
        p95_idx = min(int(0.95 * n), n - 1)

        latency_summary = {
            "retrieval_mean_sec": round(sum(ret_lats) / n, 3),
            "generation_mean_sec": round(sum(gen_lats) / n, 3),
            "total_mean_sec": round(sum(tot_lats) / n, 3),
            "total_min_sec": min(tot_lats),
            "total_max_sec": max(tot_lats),
            "total_p50_sec": tot_lats_sorted[p50_idx],
            "total_p95_sec": tot_lats_sorted[p95_idx],
        }

        # Category Breakdown
        categories = sorted(list({r["category"] for r in results}))
        category_breakdown: Dict[str, Dict[str, float]] = {}
        for cat in categories:
            cat_samples = [r for r in results if r["category"] == cat]
            cn = len(cat_samples)
            category_breakdown[cat] = {
                "count": cn,
                "faithfulness": round(sum(s["faithfulness"] for s in cat_samples) / cn, 4),
                "context_precision": round(sum(s["context_precision"] for s in cat_samples) / cn, 4),
                "context_recall": round(sum(s["context_recall"] for s in cat_samples) / cn, 4),
                "answer_relevance": round(sum(s["answer_relevance"] for s in cat_samples) / cn, 4),
                "answer_correctness": round(sum(s["answer_correctness"] for s in cat_samples) / cn, 4),
                "citation_accuracy": round(sum(s["citation_accuracy"] for s in cat_samples) / cn, 4),
                "total_mean_latency_sec": round(sum(s["total_latency_sec"] for s in cat_samples) / cn, 3),
            }

        return {
            "model_name": settings.OPENROUTER_MODEL if not self.mock_mode else "Mock-Deterministic-LLM",
            "mock_mode": self.mock_mode,
            "target_document_id": self.target_document_id,
            "overall_metrics": overall_metrics,
            "latency_summary": latency_summary,
            "target_thresholds": TARGET_METRIC_THRESHOLDS,
            "category_breakdown": category_breakdown,
            "results": results,
        }
