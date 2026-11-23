import React, { useState, useEffect } from 'react';
import { 
  X, FileText, ChevronLeft, ChevronRight, Search, 
  Copy, Sparkles, Table as TableIcon, Hash, Check
} from 'lucide-react';
import type { UploadedFile, Citation, DocumentSummaryResponse } from '../types/chat';
import { api } from '../services/api';

interface DocumentViewerDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  file: UploadedFile | null;
  activeCitation?: Citation | null;
}

export const DocumentViewerDrawer: React.FC<DocumentViewerDrawerProps> = ({
  isOpen,
  onClose,
  file,
  activeCitation
}) => {
  const [currentPage, setCurrentPage] = useState<number>(activeCitation?.pageNumber || 1);
  const [searchDocQuery, setSearchDocQuery] = useState('');
  const [activeViewMode, setActiveViewMode] = useState<'text' | 'tables' | 'chunks'>('text');
  const [copied, setCopied] = useState(false);
  const [summaryDetail, setSummaryDetail] = useState<DocumentSummaryResponse | null>(null);

  useEffect(() => {
    if (!file) {
      setSummaryDetail(null);
      return;
    }
    let isCurrent = true;
    api.getDocumentSummary(file.id)
      .then((data) => {
        if (isCurrent) setSummaryDetail(data);
      })
      .catch(() => {});
    return () => {
      isCurrent = false;
    };
  }, [file]);

  if (!isOpen || !file) return null;

  const handleCopyPageText = () => {
    navigator.clipboard.writeText(file.contentSnippet || 'Document content preview...');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="w-full lg:w-[480px] xl:w-[560px] h-full bg-slate-950/95 border-l border-slate-800/80 flex flex-col z-30 transition-all duration-300 animate-in slide-in-from-right">
      
      {/* Header bar */}
      <div className="flex items-center justify-between p-4 border-b border-slate-800/80 bg-slate-900/60">
        <div className="flex items-center gap-3 min-w-0">
          <div className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <FileText className="w-5 h-5" />
          </div>
          <div className="min-w-0 flex-1">
            <h3 className="text-sm font-bold text-slate-100 truncate" title={file.name}>
              {file.name}
            </h3>
            <p className="text-[11px] text-slate-400">
              {file.pages ? `${file.pages} pages` : 'Document'} • {file.size}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={handleCopyPageText}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            title="Copy Page Text"
          >
            {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
          </button>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* View Mode Switcher */}
      <div className="flex items-center justify-between px-4 py-2 bg-slate-900/40 border-b border-slate-800/60 text-xs">
        <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveViewMode('text')}
            className={`px-3 py-1 rounded-lg font-medium transition-all ${
              activeViewMode === 'text' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Parsed Text
          </button>
          <button
            onClick={() => setActiveViewMode('tables')}
            className={`px-3 py-1 rounded-lg font-medium transition-all ${
              activeViewMode === 'tables' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Tables (2)
          </button>
          <button
            onClick={() => setActiveViewMode('chunks')}
            className={`px-3 py-1 rounded-lg font-medium transition-all ${
              activeViewMode === 'chunks' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Vector Chunks
          </button>
        </div>

        {/* Page Navigator */}
        {file.pages && (
          <div className="flex items-center gap-2 text-slate-400">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage <= 1}
              className="p-1 rounded hover:bg-slate-800 disabled:opacity-30"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="font-mono text-[11px] text-slate-300">
              {currentPage} / {file.pages}
            </span>
            <button
              onClick={() => setCurrentPage(Math.min(file.pages || 1, currentPage + 1))}
              disabled={currentPage >= (file.pages || 1)}
              className="p-1 rounded hover:bg-slate-800 disabled:opacity-30"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* Search in document */}
      <div className="px-4 py-2 border-b border-slate-800/60 bg-slate-950">
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search keywords inside document..."
            value={searchDocQuery}
            onChange={(e) => setSearchDocQuery(e.target.value)}
            className="w-full bg-slate-900 text-xs text-slate-200 placeholder-slate-500 rounded-xl pl-9 pr-3 py-1.5 border border-slate-800 focus:outline-none focus:border-indigo-500/50"
          />
        </div>
      </div>

      {/* Main Document Content Display Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 font-sans text-slate-300 text-xs leading-relaxed">
        
        {/* Highlight Banner if triggered by citation click */}
        {activeCitation && (
          <div className="p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-200 space-y-1 animate-pulse">
            <div className="font-bold flex items-center gap-1.5 text-xs text-indigo-400">
              <Sparkles className="w-3.5 h-3.5" /> Citation Active Match (Page {activeCitation.pageNumber})
            </div>
            <p className="text-[11px] italic">"{activeCitation.snippet}"</p>
          </div>
        )}

        {/* Page-Specific AI Summary if Available */}
        {(() => {
          const pageSum = summaryDetail?.page_summaries?.find(p => p.page_number === currentPage);
          if (!pageSum || !pageSum.summary) return null;
          return (
            <div className="p-3.5 rounded-2xl bg-indigo-950/40 border border-indigo-500/30 space-y-1.5 animate-in fade-in">
              <div className="flex items-center justify-between text-[11px] font-bold uppercase tracking-wider text-indigo-400">
                <span className="flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-400" /> Page {currentPage} AI Summary
                </span>
                <span className="font-mono text-[10px] text-indigo-300">
                  {pageSum.estimated_tokens ? `~${pageSum.estimated_tokens} tokens` : ''}
                </span>
              </div>
              <p className="text-slate-200 leading-relaxed text-xs whitespace-pre-wrap">
                {pageSum.summary}
              </p>
            </div>
          );
        })()}

        {/* Executive Summary Card */}
        {file.summary && (
          <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1.5">
            <div className="text-[11px] font-bold uppercase tracking-wider text-indigo-400">
              DocMind AI Summary
            </div>
            <p className="text-slate-300 leading-relaxed text-xs">{file.summary}</p>
          </div>
        )}

        {/* View Mode Content */}
        {activeViewMode === 'text' && (
          <div className="space-y-4">
            <div className="p-4 rounded-2xl bg-slate-900/50 border border-slate-800/80 space-y-3 font-mono text-[11px] leading-relaxed">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2 text-slate-400 font-sans">
                <span className="font-bold text-slate-200">PAGE {currentPage} CONTENT</span>
                <span>Tokens: ~420</span>
              </div>
              <p className="text-slate-200">
                {activeCitation?.snippet || file.contentSnippet || `[PAGE ${currentPage} TEXT] Document content for page ${currentPage}.`}
              </p>
              {file.summary && (
                <p className="text-slate-400">
                  {file.summary}
                </p>
              )}
            </div>
          </div>
        )}

        {activeViewMode === 'tables' && (
          <div className="space-y-3">
            <div className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
              <TableIcon className="w-4 h-4 text-amber-400" /> Extracted Structured Table (Page 4)
            </div>
            <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/60">
              <table className="w-full text-left text-[11px]">
                <thead className="bg-slate-900 border-b border-slate-800 text-slate-400">
                  <tr>
                    <th className="p-2.5">Category</th>
                    <th className="p-2.5">Q3 2024</th>
                    <th className="p-2.5">Q3 2025</th>
                    <th className="p-2.5">YoY Growth</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-200">
                  <tr>
                    <td className="p-2.5 font-medium">Enterprise ARR</td>
                    <td className="p-2.5">$25.8M</td>
                    <td className="p-2.5">$32.1M</td>
                    <td className="p-2.5 text-emerald-400 font-bold">+24.4%</td>
                  </tr>
                  <tr>
                    <td className="p-2.5 font-medium">Professional Services</td>
                    <td className="p-2.5">$15.2M</td>
                    <td className="p-2.5">$16.5M</td>
                    <td className="p-2.5 text-emerald-400 font-bold">+8.5%</td>
                  </tr>
                  <tr>
                    <td className="p-2.5 font-medium">Operating Expenses</td>
                    <td className="p-2.5">$11.1M</td>
                    <td className="p-2.5">$12.5M</td>
                    <td className="p-2.5 text-amber-400">+12.6%</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeViewMode === 'chunks' && (
          <div className="space-y-3">
            <div className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
              <Hash className="w-4 h-4 text-cyan-400" /> Vector Database Chunks (HNSW Index)
            </div>
            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 font-mono text-[10px] space-y-1.5 text-slate-400">
              <div className="text-cyan-400 font-bold">CHUNK_ID: #vector-89412a (Cosine Similarity: 0.942)</div>
              <p className="text-slate-300">"Total net revenue for Q3 2025 reached $48.6 Million, representing an 18.4% year-over-year increase..."</p>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 font-mono text-[10px] space-y-1.5 text-slate-400">
              <div className="text-cyan-400 font-bold">CHUNK_ID: #vector-89412b (Cosine Similarity: 0.887)</div>
              <p className="text-slate-300">"Operating expenses totalled $12.5M, with R&D allocation rising to $8.4M for Next-Gen vector search infrastructure."</p>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};
