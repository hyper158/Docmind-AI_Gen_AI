import type {
  UploadedFile,
  ChatMessage,
  ChatSession,
  Citation,
  EvaluationRunDetail,
  EvaluationSummaryResponse,
  EvaluationHistoryResponse,
  TestCaseResult,
} from '../types/chat';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export interface BackendDocument {
  document_id: string;
  filename: string;
  original_filename: string;
  file_path: string;
  file_hash: string;
  upload_timestamp: string;
  processing_status: string;
  page_count: number;
  chunk_count: number;
  file_size: number;
  summary?: string;
  content_snippet?: string;
}

export interface BackendCitation {
  citation_id: string;
  document_id: string;
  filename: string;
  page_number: number;
  chunk_id: string;
  relevant_text_snippet: string;
  relevance_score?: number;
}

export interface BackendChatResponse {
  answer: string;
  session_id: string;
  message_id: string;
  citations: BackendCitation[];
  answer_status: string;
  retrieved_source_count: number;
  thinking_process?: string;
  reasoning_time?: number;
}

export interface BackendMessage {
  message_id: string;
  session_id: string;
  role: 'user' | 'assistant';
  message_content: string;
  created_at: string;
  citations?: BackendCitation[];
  thinking_process?: string;
  reasoning_time?: number;
}

export interface BackendSession {
  session_id: string;
  session_name: string;
  created_at: string;
  updated_at: string;
  documents: BackendDocument[];
  messages: BackendMessage[];
}

// Convert byte size to readable string
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

// Map BackendDocument to frontend UploadedFile
export function mapDocumentToFile(doc: BackendDocument): UploadedFile {
  let status: 'ready' | 'indexing' | 'error' = 'ready';
  if (doc.processing_status === 'processing' || doc.processing_status === 'uploaded') {
    status = 'indexing';
  } else if (doc.processing_status === 'failed') {
    status = 'error';
  }

  return {
    id: doc.document_id,
    name: doc.original_filename || doc.filename,
    size: formatBytes(doc.file_size),
    type: 'pdf',
    pages: doc.page_count,
    uploadedAt: new Date(doc.upload_timestamp).toLocaleDateString([], {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }),
    status,
    summary: doc.summary,
    tokensCount: doc.chunk_count * 120, // Approx ~120 tokens per chunk
    contentSnippet: doc.content_snippet,
  };
}

// Map BackendCitation to frontend Citation
export function mapBackendCitation(c: BackendCitation): Citation {
  return {
    id: c.citation_id,
    fileId: c.document_id,
    fileName: c.filename,
    pageNumber: c.page_number,
    snippet: c.relevant_text_snippet,
    relevanceScore: c.relevance_score,
  };
}

// Map BackendMessage to frontend ChatMessage
export function mapBackendMessage(msg: BackendMessage): ChatMessage {
  return {
    id: msg.message_id,
    sender: msg.role === 'user' ? 'user' : 'assistant',
    content: msg.message_content,
    timestamp: new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    citations: (msg.citations || []).map(mapBackendCitation),
    thinkingProcess: msg.thinking_process,
    reasoningTime: msg.reasoning_time,
  };
}

// Map BackendSession to frontend ChatSession
export function mapBackendSession(s: BackendSession): ChatSession {
  return {
    id: s.session_id,
    title: s.session_name,
    updatedAt: new Date(s.updated_at).toLocaleDateString([], {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }),
    files: s.documents.map(mapDocumentToFile),
    messages: s.messages.map(mapBackendMessage),
    model: 'docmind-pro-v4',
  };
}

export const api = {
  // Health
  async checkHealth(): Promise<{ status: string; service: string; version: string }> {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (!res.ok) throw new Error('Backend health check failed');
    return res.json();
  },

  // Documents
  async uploadDocument(file: File): Promise<UploadedFile> {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${API_BASE_URL}/documents/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Upload failed with status ${res.status}`);
    }

    const doc: BackendDocument = await res.json();
    return mapDocumentToFile(doc);
  },

  async getDocuments(): Promise<UploadedFile[]> {
    const res = await fetch(`${API_BASE_URL}/documents`);
    if (!res.ok) throw new Error('Failed to fetch documents');
    const data: { documents: BackendDocument[]; total_count: number } = await res.json();
    return data.documents.map(mapDocumentToFile);
  },

  async deleteDocument(documentId: string): Promise<void> {
    const res = await fetch(`${API_BASE_URL}/documents/${documentId}`, {
      method: 'DELETE',
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || 'Failed to delete document');
    }
  },

  // Chat
  async sendMessage(params: {
    question: string;
    sessionId?: string;
    selectedDocumentIds?: string[];
  }): Promise<BackendChatResponse> {
    const res = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question: params.question,
        session_id: params.sessionId,
        selected_document_ids: params.selectedDocumentIds || [],
      }),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Chat request failed: ${res.status}`);
    }

    return res.json();
  },

  // Sessions
  async getSessions(): Promise<ChatSession[]> {
    const res = await fetch(`${API_BASE_URL}/sessions`);
    if (!res.ok) throw new Error('Failed to fetch chat sessions');
    const data: { sessions: BackendSession[]; total_count: number } = await res.json();
    return data.sessions.map(mapBackendSession);
  },

  async createSession(name?: string, documentIds?: string[]): Promise<ChatSession> {
    const res = await fetch(`${API_BASE_URL}/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_name: name || 'New Study Session',
        document_ids: documentIds || [],
      }),
    });
    if (!res.ok) throw new Error('Failed to create session');
    const s: BackendSession = await res.json();
    return mapBackendSession(s);
  },

  async deleteSession(sessionId: string): Promise<void> {
    const res = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete session');
  },

  // Evaluation
  async getEvaluationSummary(): Promise<EvaluationSummaryResponse> {
    const res = await fetch(`${API_BASE_URL}/evaluation/summary`);
    if (!res.ok) throw new Error('Failed to fetch evaluation summary');
    return res.json();
  },

  async getEvaluationHistory(): Promise<EvaluationHistoryResponse> {
    const res = await fetch(`${API_BASE_URL}/evaluation/history`);
    if (!res.ok) throw new Error('Failed to fetch evaluation history');
    return res.json();
  },

  async getEvaluationResults(params?: { category?: string; limit?: number }): Promise<{
    run_id: string;
    total_count: number;
    results: TestCaseResult[];
  }> {
    const query = new URLSearchParams();
    if (params?.category) query.append('category', params.category);
    if (params?.limit) query.append('limit', params.limit.toString());
    const url = `${API_BASE_URL}/evaluation/results${query.toString() ? '?' + query.toString() : ''}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch evaluation results');
    return res.json();
  },

  async startEvaluation(params: {
    mock_mode: boolean;
    limit?: number;
    category?: string;
  }): Promise<{ run_id: string; status: string; message: string }> {
    const res = await fetch(`${API_BASE_URL}/evaluation/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || 'Failed to start evaluation');
    }
    return res.json();
  },

  async getEvaluationRun(runId: string): Promise<EvaluationRunDetail> {
    const res = await fetch(`${API_BASE_URL}/evaluation/run/${runId}`);
    if (!res.ok) throw new Error('Failed to fetch evaluation run');
    return res.json();
  },
};
