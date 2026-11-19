import type { ChatSession, AIModel, UploadedFile } from '../types/chat';

export const AI_MODELS: AIModel[] = [
  {
    id: 'docmind-pro-v4',
    name: 'DocMind Pro 4.5',
    description: 'Best for complex PDF analysis, cross-document reasoning & table extraction',
    iconName: 'Sparkles',
    badge: 'Recommended',
    contextWindow: '200k tokens',
    speed: 'Ultra Fast'
  },
  {
    id: 'claude-3-5-sonnet',
    name: 'Claude 3.5 Sonnet',
    description: 'Exceptional visual analysis, code review, and nuanced legal/technical comprehension',
    iconName: 'Cpu',
    badge: 'Popular',
    contextWindow: '200k tokens',
    speed: 'Fast'
  },
  {
    id: 'gpt-4o',
    name: 'GPT-4o Omnimodal',
    description: 'High intelligence model for general multi-format document Q&A',
    iconName: 'Zap',
    badge: 'Powerful',
    contextWindow: '128k tokens',
    speed: 'Very Fast'
  },
  {
    id: 'deepseek-r1-doc',
    name: 'DeepSeek R1 Reasoner',
    description: 'Deep mathematical & structural logic reasoning over research papers & codebases',
    iconName: 'Brain',
    badge: 'Deep Reasoner',
    contextWindow: '128k tokens',
    speed: 'Thoughtful'
  }
];

export const INITIAL_FILES: UploadedFile[] = [
  {
    id: 'file-1',
    name: 'Q3_2025_Financial_Report.pdf',
    size: '4.2 MB',
    type: 'pdf',
    pages: 28,
    uploadedAt: '10 minutes ago',
    status: 'ready',
    summary: 'Comprehensive Q3 fiscal review detailing revenue growth (+18.4%), operational expenses ($12.5M), EBITDA margins, and APAC market expansion strategies.',
    tokensCount: 42300,
    contentSnippet: 'SECTION 3.2: REVENUE ANALYSIS - Total net revenue for Q3 2025 reached $48.6 Million, representing an 18.4% year-over-year increase driven primarily by Enterprise Cloud Subscriptions...'
  },
  {
    id: 'file-2',
    name: 'System_Architecture_V2.docx',
    size: '1.8 MB',
    type: 'docx',
    pages: 14,
    uploadedAt: '1 hour ago',
    status: 'ready',
    summary: 'Technical architecture specification outlining microservices, Redis caching layer, Vector DB retrieval pipelines, and OAuth2 security compliance.',
    tokensCount: 18400,
    contentSnippet: 'Architecture Diagram & Protocol Specs: User requests travel through Cloudflare API Gateway into the Document Ingestion Service, where chunking occurs using Hybrid BM25 + Vector Embeddings.'
  },
  {
    id: 'file-3',
    name: 'Machine_Learning_Pipeline.py',
    size: '340 KB',
    type: 'code',
    pages: 6,
    uploadedAt: 'Yesterday',
    status: 'ready',
    summary: 'PyTorch transformer pipeline implementation for document OCR, layout detection, text chunking, and embedding generation using HuggingFace models.',
    tokensCount: 8200,
    contentSnippet: 'def extract_tabular_data(pdf_stream: BytesIO) -> List[pd.DataFrame]:\n    # Uses LayoutLMv3 + Tabula for structured table parsing\n    table_extractor = TableTransformer.from_pretrained("microsoft/table-transformer-detection")\n    ...'
  }
];

export const INITIAL_SESSIONS: ChatSession[] = [
  {
    id: 'session-1',
    title: 'Financial Q3 Report Deep Dive',
    updatedAt: '2 mins ago',
    pinned: true,
    category: 'Finance',
    model: 'docmind-pro-v4',
    files: [INITIAL_FILES[0]],
    messages: [
      {
        id: 'm1',
        sender: 'user',
        content: 'Hi! Can you give me a summary of the Q3 revenue growth and main expense drivers from the attached report?',
        timestamp: '10:42 AM',
        attachedFiles: [INITIAL_FILES[0]]
      },
      {
        id: 'm2',
        sender: 'assistant',
        content: `Here is the executive summary based on **Q3_2025_Financial_Report.pdf**:

### 📈 Revenue Overview
- **Total Revenue**: **$48.6 Million**, reflecting an **18.4% YoY increase**.
- **Primary Driver**: Enterprise Cloud Subscriptions accounted for **$32.1M** (66% of total revenue), growing 24% YoY.
- **Secondary Driver**: Professional Services & API Licensing generated **$16.5M**.

---

### 💵 Expense Analysis & Margin Highlights
1. **R&D Investments**: Increased by **12%** ($8.4M) dedicated to AI/ML infrastructure.
2. **Sales & Marketing**: Operating cost was **$12.5M**, maintaining an efficient CAC payback period of 8 months.
3. **EBITDA Margin**: Expanded to **24.5%** (up 310 bps compared to Q2 2025).

> **Key Takeaway**: The company is scaling enterprise ARR rapidly while keeping operating margin expansion healthy.`,
        timestamp: '10:43 AM',
        attachedFiles: [INITIAL_FILES[0]],
        reasoningTime: 1.8,
        thinkingProcess: 'Scanned pages 3-12 of Q3_2025_Financial_Report.pdf. Extracted table 2.1 (Revenue Breakdown) and section 3.4 (Operating Expenses). Computed percentage margins.',
        citations: [
          {
            id: 'c1',
            fileId: 'file-1',
            fileName: 'Q3_2025_Financial_Report.pdf',
            pageNumber: 4,
            snippet: 'Net revenue for Q3 2025 stood at $48.6M (+18.4% YoY), propelled by Enterprise Cloud ARR scaling.'
          },
          {
            id: 'c2',
            fileId: 'file-1',
            fileName: 'Q3_2025_Financial_Report.pdf',
            pageNumber: 9,
            snippet: 'Operating expenses totalled $12.5M, with R&D allocation rising to $8.4M for Next-Gen vector search infrastructure.'
          }
        ]
      }
    ]
  },
  {
    id: 'session-2',
    title: 'Architecture Spec & Vector DB Review',
    updatedAt: '1 hour ago',
    pinned: false,
    category: 'Engineering',
    model: 'claude-3-5-sonnet',
    files: [INITIAL_FILES[1]],
    messages: [
      {
        id: 'm3',
        sender: 'user',
        content: 'How does the document ingestion pipeline handle large PDFs according to the spec?',
        timestamp: '09:15 AM',
        attachedFiles: [INITIAL_FILES[1]]
      },
      {
        id: 'm4',
        sender: 'assistant',
        content: `According to **System_Architecture_V2.docx**, the document ingestion pipeline uses a multi-tier hybrid chunking architecture:

1. **Preprocessing & Layout Parse**: Documents above 50 pages are split asynchronously using AWS Lambda workers.
2. **Hybrid Chunking**: Combines semantic paragraph splitting with 512-token rolling windows and 50-token overlap.
3. **Vector Indexing**: Embedded using \`text-embedding-3-large\` and indexed into Qdrant vector store with HNSW indexing.`,
        timestamp: '09:16 AM',
        attachedFiles: [INITIAL_FILES[1]],
        reasoningTime: 2.1,
        citations: [
          {
            id: 'c3',
            fileId: 'file-2',
            fileName: 'System_Architecture_V2.docx',
            pageNumber: 5,
            snippet: 'Ingestion pipeline utilizes async worker pools to split large PDF blobs into 512-token chunks with HNSW vector indexing.'
          }
        ]
      }
    ]
  },
  {
    id: 'session-3',
    title: 'Python ML Pipeline Code Inspection',
    updatedAt: 'Yesterday',
    pinned: false,
    category: 'Code',
    model: 'deepseek-r1-doc',
    files: [INITIAL_FILES[2]],
    messages: []
  }
];

export const SAMPLE_PROMPT_SUGGESTIONS = [
  {
    icon: 'FileText',
    title: 'Summarize Key Insights',
    prompt: 'Can you provide a comprehensive summary of this document, highlighting the key findings and conclusions?',
    category: 'Overview'
  },
  {
    icon: 'Table',
    title: 'Extract Tables & Data',
    prompt: 'Extract all numerical metrics, financial figures, and structured table data from this file into a clear list.',
    category: 'Data'
  },
  {
    icon: 'AlertTriangle',
    title: 'Identify Risks & Clause Warnings',
    prompt: 'Scan this document for potential risk factors, legal compliance issues, or critical warnings mentioned.',
    category: 'Analysis'
  },
  {
    icon: 'HelpCircle',
    title: 'Generate Q&A Study Guide',
    prompt: 'Based on this document, generate 5 key questions and detailed answers to test my understanding of the material.',
    category: 'Study'
  }
];
