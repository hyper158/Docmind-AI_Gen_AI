export type FileType = 'pdf' | 'docx' | 'txt' | 'csv' | 'json' | 'code' | 'image';

export interface UploadedFile {
  id: string;
  name: string;
  size: string;
  type: FileType;
  pages?: number;
  uploadedAt: string;
  status: 'ready' | 'indexing' | 'error';
  summary?: string;
  tokensCount?: number;
  url?: string;
  contentSnippet?: string;
}

export interface Citation {
  id: string;
  fileId: string;
  fileName: string;
  pageNumber?: number;
  snippet: string;
  relevanceScore?: number;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  content: string;
  timestamp: string;
  attachedFiles?: UploadedFile[];
  citations?: Citation[];
  reasoningTime?: number;
  thinkingProcess?: string;
  feedback?: 'like' | 'dislike' | null;
  copied?: boolean;
}

export interface ChatSession {
  id: string;
  title: string;
  updatedAt: string;
  files: UploadedFile[];
  messages: ChatMessage[];
  model: string;
  pinned?: boolean;
  category?: string;
}

export interface AIModel {
  id: string;
  name: string;
  description: string;
  iconName: string;
  badge?: string;
  contextWindow: string;
  speed: string;
}

// === Evaluation Types ===

export interface EvaluationMetrics {
  faithfulness: number;
  context_precision: number;
  context_recall: number;
  answer_relevance: number;
  answer_correctness: number;
  citation_accuracy: number;
  out_of_syllabus_accuracy: number;
  no_document_accuracy: number;
  total_evaluated: number;
}

export interface LatencySummary {
  retrieval_mean_sec: number;
  generation_mean_sec: number;
  total_mean_sec: number;
  total_min_sec: number;
  total_max_sec: number;
  total_p50_sec: number;
  total_p95_sec: number;
}

export interface CategoryScore {
  count: number;
  faithfulness: number;
  context_precision: number;
  context_recall: number;
  answer_relevance: number;
  answer_correctness: number;
  citation_accuracy: number;
  total_mean_latency_sec: number;
}

export interface TestCaseResult {
  id: string;
  category: string;
  question: string;
  ground_truth_answer: string;
  generated_answer: string;
  answer_status: string;
  retrieved_chunk_count: number;
  citation_count: number;
  citations?: any[];
  retrieval_latency_sec: number;
  generation_latency_sec: number;
  total_latency_sec: number;
  context_precision: number;
  context_recall: number;
  faithfulness: number;
  answer_relevance: number;
  answer_correctness: number;
  citation_accuracy: number;
  out_of_syllabus_accuracy: number;
  no_document_accuracy: number;
}

export interface EvaluationRunSummary {
  run_id: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  model_name: string;
  mock_mode: boolean;
  total_questions: number;
  overall_metrics: EvaluationMetrics | null;
  latency_summary?: LatencySummary | null;
  duration_sec: number | null;
  error_message: string | null;
}

export interface EvaluationRunDetail {
  run_id: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  model_name: string;
  embedding_model: string;
  mock_mode: boolean;
  target_document_id: string;
  dataset_name: string;
  total_questions: number;
  overall_metrics: EvaluationMetrics;
  latency_summary: LatencySummary;
  target_thresholds: Record<string, number>;
  category_breakdown: Record<string, CategoryScore>;
  results: TestCaseResult[];
  duration_sec: number | null;
  error_message: string | null;
}

export interface EvaluationSummaryResponse {
  has_evaluation: boolean;
  latest_run: EvaluationRunDetail | null;
}

export interface EvaluationHistoryResponse {
  runs: EvaluationRunSummary[];
  total_count: number;
}

// === Hierarchical Document Summarization Types ===

export interface PageSummary {
  page_number: number;
  summary: string;
  status: 'completed' | 'empty' | 'insufficient_text' | 'failed' | 'partial';
  is_chunked?: boolean;
  chunk_count?: number;
  input_characters?: number;
  estimated_tokens?: number;
  processing_time_sec?: number;
  error_message?: string | null;
}

export interface SummaryMetadata {
  document_id: string;
  filename: string;
  total_pages: number;
  successful_pages: number;
  empty_pages?: number;
  insufficient_text_pages?: number;
  failed_pages?: number;
  total_characters?: number;
  total_words?: number;
  is_scanned_or_image?: boolean;
  total_duration_sec?: number;
  aggregation_levels?: number;
  section_count?: number;
  model_name?: string;
  completed_at?: string;
}

export interface SummarizationProgress {
  document_id: string;
  filename?: string;
  status: 'idle' | 'processing' | 'completed' | 'failed' | 'partial';
  stage: 'idle' | 'extraction' | 'page_summarization' | 'hierarchical_aggregation' | 'completed' | 'failed';
  total_pages: number;
  processed_pages: number;
  failed_pages: number;
  percent_complete: number;
  started_at?: string;
  error_message?: string | null;
}

export interface DocumentSummaryResponse {
  document_id: string;
  filename?: string;
  status: string;
  final_summary?: string | null;
  page_summaries: PageSummary[];
  metadata?: SummaryMetadata | null;
  progress?: SummarizationProgress | null;
  error_message?: string | null;
}


