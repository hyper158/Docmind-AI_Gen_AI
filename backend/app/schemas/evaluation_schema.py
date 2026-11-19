from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class EvaluationMetrics(BaseModel):
    faithfulness: float = 0.0
    context_precision: float = 0.0
    context_recall: float = 0.0
    answer_relevance: float = 0.0
    answer_correctness: float = 0.0
    citation_accuracy: float = 0.0
    out_of_syllabus_accuracy: float = 0.0
    no_document_accuracy: float = 0.0
    total_evaluated: int = 0


class LatencySummary(BaseModel):
    retrieval_mean_sec: float = 0.0
    generation_mean_sec: float = 0.0
    total_mean_sec: float = 0.0
    total_min_sec: float = 0.0
    total_max_sec: float = 0.0
    total_p50_sec: float = 0.0
    total_p95_sec: float = 0.0


class CategoryScore(BaseModel):
    count: int = 0
    faithfulness: float = 0.0
    context_precision: float = 0.0
    context_recall: float = 0.0
    answer_relevance: float = 0.0
    answer_correctness: float = 0.0
    citation_accuracy: float = 0.0
    total_mean_latency_sec: float = 0.0


class TestCaseResult(BaseModel):
    id: str
    category: str
    question: str
    ground_truth_answer: str
    generated_answer: str
    answer_status: str
    retrieved_chunk_count: int = 0
    citation_count: int = 0
    citations: Optional[List[Any]] = Field(default_factory=list)
    retrieval_latency_sec: float = 0.0
    generation_latency_sec: float = 0.0
    total_latency_sec: float = 0.0
    context_precision: float = 0.0
    context_recall: float = 0.0
    faithfulness: float = 0.0
    answer_relevance: float = 0.0
    answer_correctness: float = 0.0
    citation_accuracy: float = 0.0
    out_of_syllabus_accuracy: float = 0.0
    no_document_accuracy: float = 0.0


class EvaluationRunSummary(BaseModel):
    """Summary of one evaluation run for history listing."""
    run_id: str
    status: str  # pending, running, completed, failed
    started_at: str
    completed_at: Optional[str] = None
    model_name: str = ""
    mock_mode: bool = False
    total_questions: int = 0
    overall_metrics: Optional[EvaluationMetrics] = None
    latency_summary: Optional[LatencySummary] = None
    duration_sec: Optional[float] = None
    error_message: Optional[str] = None


class EvaluationRunDetail(BaseModel):
    """Full detail of a single evaluation run."""
    run_id: str
    status: str  # pending, running, completed, failed
    started_at: str
    completed_at: Optional[str] = None
    model_name: str = ""
    embedding_model: str = ""
    mock_mode: bool = False
    target_document_id: str = ""
    dataset_name: str = ""
    total_questions: int = 0
    overall_metrics: EvaluationMetrics = Field(default_factory=EvaluationMetrics)
    latency_summary: LatencySummary = Field(default_factory=LatencySummary)
    target_thresholds: Dict[str, float] = Field(default_factory=dict)
    category_breakdown: Dict[str, CategoryScore] = Field(default_factory=dict)
    results: List[TestCaseResult] = Field(default_factory=list)
    duration_sec: Optional[float] = None
    error_message: Optional[str] = None


class EvaluationSummaryResponse(BaseModel):
    """Response for GET /api/evaluation/summary - latest run summary."""
    has_evaluation: bool = False
    latest_run: Optional[EvaluationRunDetail] = None


class EvaluationHistoryResponse(BaseModel):
    """Response for GET /api/evaluation/history."""
    runs: List[EvaluationRunSummary] = Field(default_factory=list)
    total_count: int = 0


class StartEvaluationRequest(BaseModel):
    mock_mode: bool = False
    limit: Optional[int] = None
    category: Optional[str] = None


class StartEvaluationResponse(BaseModel):
    run_id: str
    status: str
    message: str
