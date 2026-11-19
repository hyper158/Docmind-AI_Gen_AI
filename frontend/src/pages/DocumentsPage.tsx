import React, { useState } from 'react';
import { 
  FolderKanban, UploadCloud, Search, 
  FileText, HardDrive, Sparkles, MessageSquare, 
  Eye, Trash2
} from 'lucide-react';
import type { UploadedFile } from '../types/chat';
import { getFileIcon } from '../components/FileBadge';

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

  const totalTokens = files.reduce((acc, f) => acc + (f.tokensCount || 0), 0);
  const totalPages = files.reduce((acc, f) => acc + (f.pages || 0), 0);

  const filteredFiles = files.filter(file => {
    const matchesSearch = file.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (file.summary && file.summary.toLowerCase().includes(searchQuery.toLowerCase()));
    
    if (selectedFilter === 'all') return matchesSearch;
    return matchesSearch && file.type === selectedFilter;
  });

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
            Manage your vector-indexed files, inspect chunk summaries, and trigger Q&A chats.
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
                <span className="px-2 py-0.5 text-[10px] uppercase font-bold tracking-wider rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                  {file.status}
                </span>
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
                  className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                  title="Inspect summary"
                >
                  <Eye className="w-4 h-4" />
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

      {/* Inspection Modal */}
      {previewModalFile && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-slate-100">{previewModalFile.name}</h3>
              <button onClick={() => setPreviewModalFile(null)} className="text-slate-400 hover:text-white">✕</button>
            </div>
            <div className="text-xs text-slate-300 space-y-2">
              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                <div className="font-bold text-indigo-400 mb-1">AI Extracted Summary:</div>
                <p>{previewModalFile.summary}</p>
              </div>
              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                <div className="font-bold text-cyan-400 mb-1">Text Snippet:</div>
                <p className="font-mono text-[11px] text-slate-400">{previewModalFile.contentSnippet}</p>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
