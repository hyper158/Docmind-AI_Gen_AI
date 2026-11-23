import React, { useState, useEffect, useRef } from 'react';
import { 
  FolderKanban, UploadCloud, Search, 
  FileText, HardDrive, Sparkles, MessageSquare, 
  Eye, Trash2, Copy, Check, RefreshCw, Loader2,
  BookOpen, Layers, BarChart2, AlertCircle, X
} from 'lucide-react';
import type { UploadedFile, DocumentSummaryResponse, SummarizationProgress } from '../types/chat';
import { getFileIcon } from '../components/FileBadge';
import { api } from '../services/api';

interface DocumentsPageProps {
  files: UploadedFile[];
  onOpenUploadModal: () => void;
  onSelectFileForChat: (file: UploadedFile) => void;
  onDeleteFile: (fileId: string) => void;
}

export const DocumentsPage: React.FC<DocumentsPageProps> = ({
  files,
  onOpenUploadModal,
  onSelectFileForChat,
  onDeleteFile
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilter, setSelectedFilter] = useState<string>('all');
  const [previewModalFile, setPreviewModalFile] = useState<UploadedFile | null>(null);

  // Summary Inspector Modal State
  const [summaryData, setSummaryData] = useState<DocumentSummaryResponse | null>(null);
  const [summaryLoading, setSummaryLoading] = useState<boolean>(false);
  const [summaryTab, setSummaryTab] = useState<'master' | 'pages' | 'diagnostics'>('master');
  const [selectedPageNum, setSelectedPageNum] = useState<number>(1);
  const [isSummarizing, setIsSummarizing] = useState<boolean>(false);
  const [progress, setProgress] = useState<SummarizationProgress | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [summaryError, setSummaryError] = useState<string | null>(null);

  const pollIntervalRef = useRef<any>(null);

  const totalTokens = files.reduce((acc, f) => acc + (f.tokensCount || 0), 0);
  const totalPages = files.reduce((acc, f) => acc + (f.pages || 0), 0);

  const filteredFiles = files.filter(file => {
    const matchesSearch = file.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (file.summary && file.summary.toLowerCase().includes(searchQuery.toLowerCase()));
    
    if (selectedFilter === 'all') return matchesSearch;
    return matchesSearch && file.type === selectedFilter;
  });

  // Fetch summary when modal opens
  useEffect(() => {
    if (!previewModalFile) {
      setSummaryData(null);
      setProgress(null);
      setIsSummarizing(false);
      setSummaryError(null);
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
      return;
    }

    let isMounted = true;
    setSummaryLoading(true);
    setSummaryError(null);
    setSelectedPageNum(1);

    const loadSummary = async () => {
      try {
        const data = await api.getDocumentSummary(previewModalFile.id);
        if (!isMounted) return;
        setSummaryData(data);
        if (data.status === 'processing') {
          setIsSummarizing(true);
          startPolling(previewModalFile.id);
        }
      } catch (err: any) {
        if (!isMounted) return;
        setSummaryError(err.message || 'Failed to load summary');
      } finally {
        if (isMounted) setSummaryLoading(false);
      }
    };

    loadSummary();

    return () => {
      isMounted = false;
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, [previewModalFile]);

  // Polling for progress during background summarization
  const startPolling = (docId: string) => {
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);

    pollIntervalRef.current = setInterval(async () => {
      try {
        const prog = await api.getDocumentSummaryStatus(docId);
        setProgress(prog);

        if (prog.status === 'completed' || prog.status === 'failed' || prog.status === 'partial') {
          setIsSummarizing(false);
          clearInterval(pollIntervalRef.current);
          const fullData = await api.getDocumentSummary(docId);
          setSummaryData(fullData);
        }
      } catch (err) {
        console.warn('Error polling summary progress:', err);
      }
    }, 2000);
  };

  // Trigger comprehensive summarization
  const handleTriggerSummarize = async () => {
    if (!previewModalFile || isSummarizing) return;
    try {
      setIsSummarizing(true);
      setSummaryError(null);
      const res = await api.summarizeDocument(previewModalFile.id, {
        mode: 'async',
        force_refresh: true,
      });
      if (res.progress) setProgress(res.progress);
      startPolling(previewModalFile.id);
    } catch (err: any) {
      setIsSummarizing(false);
      setSummaryError(err.message || 'Failed to start summarization');
    }
  };

  const handleCopySummary = () => {
    if (!summaryData?.final_summary) return;
    navigator.clipboard.writeText(summaryData.final_summary);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-y-auto bg-slate-950 p-4 sm:p-8 space-y-6 text-slate-100">
      
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <FolderKanban className="w-5 h-5" />
            </div>
            <h1 className="text-2xl font-extrabold text-white tracking-tight">
              Document Knowledge Base
            </h1>
          </div>
          <p className="text-xs text-slate-400">
            Manage your vector-indexed files, inspect hierarchical page summaries, and trigger Q&A chats.
          </p>
        </div>

        <button
          onClick={onOpenUploadModal}
          className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-medium text-xs shadow-lg shadow-indigo-600/25 transition-all"
        >
          <UploadCloud className="w-4 h-4" />
          <span>Upload New File</span>
        </button>
      </div>

      {/* Storage Banner Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Indexed Documents</span>
            <FileText className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-black text-white">{files.length} Files</div>
          <div className="text-[11px] text-slate-500">{totalPages} total pages extracted</div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Vector Embeddings</span>
            <Sparkles className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-black text-white">{totalTokens.toLocaleString()} Tokens</div>
          <div className="text-[11px] text-emerald-400">Ready for sub-second retrieval</div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Vector Store Status</span>
            <HardDrive className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-black text-white">FAISS Active</div>
          <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden mt-1">
            <div className="bg-cyan-400 h-full w-[100%]" />
          </div>
        </div>
      </div>

      {/* Search & Filter Toolbar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-900/50 p-3 rounded-2xl border border-slate-800">
        
        {/* Search */}
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Filter files by name or content..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-950 text-xs text-slate-200 placeholder-slate-500 rounded-xl pl-9 pr-3 py-2 border border-slate-800 focus:outline-none focus:border-indigo-500/50"
          />
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1 overflow-x-auto w-full sm:w-auto text-xs">
          {['all', 'pdf', 'docx', 'code', 'csv'].map((filter) => (
            <button
              key={filter}
              onClick={() => setSelectedFilter(filter)}
              className={`px-3 py-1.5 rounded-xl font-medium uppercase tracking-wider text-[10px] transition-all ${
                selectedFilter === filter
                  ? 'bg-indigo-600 text-white'
                  : 'bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              {filter}
            </button>
          ))}
        </div>

      </div>

      {/* Files Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredFiles.map((file) => (
          <div
            key={file.id}
            className="group flex flex-col justify-between p-5 rounded-2xl bg-slate-900/50 hover:bg-slate-900 border border-slate-800 hover:border-indigo-500/40 transition-all duration-200 hover:shadow-xl hover:shadow-indigo-500/5 space-y-4"
          >
            <div className="space-y-3">
              <div className="flex items-start justify-between gap-3">
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  {getFileIcon(file.type, "w-6 h-6")}
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="px-2 py-0.5 text-[10px] uppercase font-bold tracking-wider rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                    {file.status}
                  </span>
                </div>
              </div>

              <div>
                <h3 className="font-bold text-sm text-slate-100 group-hover:text-indigo-300 transition-colors line-clamp-1" title={file.name}>
                  {file.name}
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  {file.size} • {file.pages ? `${file.pages} pages` : 'Document'} • {file.uploadedAt}
                </p>
              </div>

              {file.summary && (
                <p className="text-xs text-slate-400 line-clamp-3 bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/80 leading-relaxed">
                  {file.summary}
                </p>
              )}
            </div>

            {/* Bottom Actions */}
            <div className="flex items-center justify-between pt-3 border-t border-slate-800/80 text-xs">
              <button
                onClick={() => onSelectFileForChat(file)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 font-semibold transition-colors"
              >
                <MessageSquare className="w-3.5 h-3.5" /> Chat Q&A
              </button>

              <div className="flex items-center gap-1">
                <button
                  onClick={() => setPreviewModalFile(file)}
                  className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl text-slate-300 hover:text-white bg-slate-800/60 hover:bg-indigo-600/30 hover:border-indigo-500/30 border border-slate-700/50 transition-all font-medium text-[11px]"
                  title="Inspect comprehensive summary & page breakdown"
                >
                  <Eye className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Summary</span>
                </button>
                <button
                  onClick={() => onDeleteFile(file.id)}
                  className="p-2 rounded-xl text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                  title="Delete file"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>

          </div>
        ))}
      </div>

      {/* Comprehensive Hierarchical Summary Inspector Modal */}
      {previewModalFile && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-slate-950/85 backdrop-blur-md animate-in fade-in">
          <div className="w-full max-w-4xl max-h-[90vh] bg-slate-900 border border-slate-800 rounded-3xl flex flex-col shadow-2xl overflow-hidden">
            
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-800/80 bg-slate-950/60 flex items-center justify-between gap-4">
              <div className="flex items-center gap-3 min-w-0">
                <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex-shrink-0">
                  <BookOpen className="w-5 h-5" />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <h2 className="font-extrabold text-base text-white truncate max-w-md" title={previewModalFile.name}>
                      {previewModalFile.name}
                    </h2>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-mono uppercase bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                      {summaryData?.status || 'Active'}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">
                    {previewModalFile.pages ? `${previewModalFile.pages} Pages` : ''} • Hierarchical Multi-Stage Synthesis
                  </p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2 flex-shrink-0">
                <button
                  onClick={handleTriggerSummarize}
                  disabled={isSummarizing}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                    isSummarizing
                      ? 'bg-slate-800 text-slate-400 cursor-not-allowed border border-slate-700'
                      : 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white shadow-md'
                  }`}
                  title="Generate or update comprehensive hierarchical summary"
                >
                  {isSummarizing ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-400" />
                      <span>Summarizing...</span>
                    </>
                  ) : (
                    <>
                      <RefreshCw className="w-3.5 h-3.5" />
                      <span>{summaryData?.final_summary ? 'Regenerate' : 'Generate'} Summary</span>
                    </>
                  )}
                </button>

                <button
                  onClick={handleCopySummary}
                  disabled={!summaryData?.final_summary}
                  className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors disabled:opacity-30"
                  title="Copy Full Summary"
                >
                  {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                </button>

                <button
                  onClick={() => setPreviewModalFile(null)}
                  className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Live Progress Bar if Summarizing */}
            {isSummarizing && (
              <div className="p-4 bg-indigo-950/40 border-b border-indigo-900/50 space-y-2 text-xs">
                <div className="flex items-center justify-between text-indigo-300">
                  <span className="flex items-center gap-2 font-medium">
                    <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
                    Stage: {progress?.stage ? progress.stage.replace(/_/g, ' ').toUpperCase() : 'PROCESSING PAGES...'}
                  </span>
                  <span className="font-mono text-indigo-200">
                    {progress?.processed_pages !== undefined ? `${progress.processed_pages} / ${progress.total_pages} Pages` : ''} ({progress?.percent_complete || 10}%)
                  </span>
                </div>
                <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden border border-indigo-900/60">
                  <div
                    className="bg-gradient-to-r from-indigo-500 via-purple-500 to-cyan-400 h-full transition-all duration-300"
                    style={{ width: `${progress?.percent_complete || 15}%` }}
                  />
                </div>
              </div>
            )}

            {/* Error Banner */}
            {summaryError && (
              <div className="p-3 mx-4 mt-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
                <span>{summaryError}</span>
              </div>
            )}

            {/* Tab Bar */}
            <div className="flex items-center gap-2 px-5 pt-3 border-b border-slate-800/80 bg-slate-950/40 text-xs">
              <button
                onClick={() => setSummaryTab('master')}
                className={`flex items-center gap-2 pb-2.5 font-semibold transition-all border-b-2 ${
                  summaryTab === 'master'
                    ? 'border-indigo-500 text-indigo-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <BookOpen className="w-4 h-4" />
                <span>Master Document Summary</span>
              </button>

              <button
                onClick={() => setSummaryTab('pages')}
                className={`flex items-center gap-2 pb-2.5 font-semibold transition-all border-b-2 ${
                  summaryTab === 'pages'
                    ? 'border-indigo-500 text-indigo-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <Layers className="w-4 h-4" />
                <span>Page-by-Page Summaries ({summaryData?.page_summaries?.length || 0})</span>
              </button>

              <button
                onClick={() => setSummaryTab('diagnostics')}
                className={`flex items-center gap-2 pb-2.5 font-semibold transition-all border-b-2 ${
                  summaryTab === 'diagnostics'
                    ? 'border-indigo-500 text-indigo-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <BarChart2 className="w-4 h-4" />
                <span>Extraction Diagnostics</span>
              </button>
            </div>

            {/* Modal Content Body */}
            <div className="flex-1 overflow-y-auto p-5 text-xs text-slate-200 leading-relaxed">
              
              {summaryLoading && !summaryData && (
                <div className="flex flex-col items-center justify-center p-12 space-y-3 text-slate-400">
                  <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
                  <p>Loading document summarization data...</p>
                </div>
              )}

              {/* TAB 1: MASTER SUMMARY */}
              {summaryTab === 'master' && (
                <div className="space-y-4">
                  {summaryData?.final_summary ? (
                    <div className="p-5 rounded-2xl bg-slate-950/80 border border-slate-800 whitespace-pre-wrap font-sans text-xs sm:text-[13px] leading-relaxed space-y-4 text-slate-200">
                      {summaryData.final_summary}
                    </div>
                  ) : (
                    <div className="text-center p-10 space-y-3 bg-slate-950/50 rounded-2xl border border-slate-800">
                      <Sparkles className="w-8 h-8 text-indigo-400 mx-auto" />
                      <h4 className="font-bold text-sm text-slate-200">No Comprehensive Summary Available</h4>
                      <p className="text-slate-400 max-w-md mx-auto text-xs">
                        This document has not been processed through the hierarchical summarization pipeline yet.
                        Click below to generate a complete multi-level summary.
                      </p>
                      <button
                        onClick={handleTriggerSummarize}
                        className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs shadow-md"
                      >
                        Generate Full Summary
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* TAB 2: PAGE-BY-PAGE SUMMARIES */}
              {summaryTab === 'pages' && (
                <div className="space-y-4">
                  {summaryData?.page_summaries && summaryData.page_summaries.length > 0 ? (
                    <div className="space-y-4">
                      {/* Page Selector Strip */}
                      <div className="flex items-center gap-1.5 overflow-x-auto pb-2 border-b border-slate-800/80">
                        {summaryData.page_summaries.map((p) => (
                          <button
                            key={p.page_number}
                            onClick={() => setSelectedPageNum(p.page_number)}
                            className={`px-3 py-1.5 rounded-xl font-mono text-[11px] font-bold flex-shrink-0 transition-all ${
                              selectedPageNum === p.page_number
                                ? 'bg-indigo-600 text-white shadow-md'
                                : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
                            }`}
                          >
                            Page {p.page_number}
                          </button>
                        ))}
                      </div>

                      {/* Selected Page Details */}
                      {(() => {
                        const activePage = summaryData.page_summaries.find(p => p.page_number === selectedPageNum) || summaryData.page_summaries[0];
                        if (!activePage) return null;

                        return (
                          <div className="p-5 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-3">
                            <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
                              <div className="flex items-center gap-2">
                                <span className="font-extrabold text-white text-sm">PAGE {activePage.page_number} SUMMARY</span>
                                <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold font-mono ${
                                  activePage.status === 'completed'
                                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                                    : activePage.status === 'empty'
                                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                                    : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                                }`}>
                                  {activePage.status}
                                </span>
                                {activePage.is_chunked && (
                                  <span className="px-2 py-0.5 rounded text-[10px] bg-purple-500/20 text-purple-300 border border-purple-500/30">
                                    {activePage.chunk_count} sub-chunks
                                  </span>
                                )}
                              </div>
                              <span className="text-[11px] text-slate-400 font-mono">
                                ~{activePage.estimated_tokens || 0} tokens • {activePage.input_characters || 0} chars
                              </span>
                            </div>

                            <div className="whitespace-pre-wrap text-slate-200 leading-relaxed text-xs sm:text-[13px]">
                              {activePage.summary}
                            </div>
                          </div>
                        );
                      })()}
                    </div>
                  ) : (
                    <div className="text-center p-10 text-slate-400">
                      No individual page summaries available yet. Click "Generate Summary" to run page extraction.
                    </div>
                  )}
                </div>
              )}

              {/* TAB 3: DIAGNOSTICS & EXTRACTION METRICS */}
              {summaryTab === 'diagnostics' && (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                    <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                      <div className="text-slate-400 text-[11px]">Total Pages</div>
                      <div className="text-2xl font-black text-white">{summaryData?.metadata?.total_pages ?? previewModalFile.pages ?? 0}</div>
                    </div>
                    <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                      <div className="text-slate-400 text-[11px]">Successfully Processed</div>
                      <div className="text-2xl font-black text-emerald-400">{summaryData?.metadata?.successful_pages ?? 0}</div>
                    </div>
                    <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                      <div className="text-slate-400 text-[11px]">Empty / Blank Pages</div>
                      <div className="text-2xl font-black text-amber-400">{summaryData?.metadata?.empty_pages ?? 0}</div>
                    </div>
                    <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                      <div className="text-slate-400 text-[11px]">Processing Time</div>
                      <div className="text-2xl font-black text-cyan-400">
                        {summaryData?.metadata?.total_duration_sec ? `${summaryData.metadata.total_duration_sec}s` : '0s'}
                      </div>
                    </div>
                  </div>

                  <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-2 text-xs">
                    <h4 className="font-bold text-slate-200">Extraction Quality Insights</h4>
                    <ul className="space-y-1.5 text-slate-400">
                      <li>• Total Extracted Characters: <span className="text-slate-200 font-mono">{summaryData?.metadata?.total_characters?.toLocaleString() ?? 0}</span></li>
                      <li>• Total Extracted Words: <span className="text-slate-200 font-mono">{summaryData?.metadata?.total_words?.toLocaleString() ?? 0}</span></li>
                      <li>• Scanned / Image Only Detected: <span className="text-slate-200 font-mono">{summaryData?.metadata?.is_scanned_or_image ? 'Yes (Requires OCR)' : 'No (Standard Text PDF)'}</span></li>
                      <li>• LLM Model Used: <span className="text-slate-200 font-mono">{summaryData?.metadata?.model_name || 'NVIDIA Nemotron 3.5 Lightning'}</span></li>
                    </ul>
                  </div>
                </div>
              )}

            </div>

          </div>
        </div>
      )}

    </div>
  );
};
