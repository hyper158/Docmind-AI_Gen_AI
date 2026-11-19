import React from 'react';
import { 
  Sparkles, UploadCloud, FileText, Table, AlertTriangle, 
  HelpCircle, ArrowRight, ShieldCheck, Zap, FileCode, Search
} from 'lucide-react';
import { SAMPLE_PROMPT_SUGGESTIONS, INITIAL_FILES } from '../data/mockData';
import type { UploadedFile } from '../types/chat';

interface WelcomeHeroProps {
  onOpenUploadModal: () => void;
  onSelectPrompt: (prompt: string) => void;
  onSelectSampleFile: (file: UploadedFile) => void;
}

export const WelcomeHero: React.FC<WelcomeHeroProps> = ({
  onOpenUploadModal,
  onSelectPrompt,
  onSelectSampleFile
}) => {
  const getPromptIcon = (iconName: string) => {
    switch (iconName) {
      case 'Table': return <Table className="w-5 h-5 text-amber-400" />;
      case 'AlertTriangle': return <AlertTriangle className="w-5 h-5 text-rose-400" />;
      case 'HelpCircle': return <HelpCircle className="w-5 h-5 text-emerald-400" />;
      default: return <FileText className="w-5 h-5 text-indigo-400" />;
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 space-y-8 animate-in fade-in duration-300">
      
      {/* Hero Title Header */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-gradient-to-r from-indigo-500/10 via-purple-500/10 to-cyan-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold glow-primary">
          <Sparkles className="w-4 h-4 text-indigo-400" />
          DocMind AI 4.5 • Instant Multi-Document Intelligence
        </div>

        <h1 className="text-3xl sm:text-5xl font-black text-white tracking-tight leading-tight">
          Upload any file & chat with your <span className="gradient-text">documents</span>
        </h1>

        <p className="text-sm sm:text-base text-slate-400 max-w-2xl mx-auto leading-relaxed">
          Upload PDFs, Word documents, research papers, CSV spreadsheets, or code. DocMind extracts exact page citations, analyzes complex tables, and answers instantly.
        </p>
      </div>

      {/* Hero Quick Dropzone Trigger Card */}
      <div 
        onClick={onOpenUploadModal}
        className="relative group p-6 sm:p-8 rounded-3xl bg-slate-900/60 border border-slate-800 hover:border-indigo-500/50 cursor-pointer transition-all duration-300 hover:shadow-2xl hover:shadow-indigo-500/10 text-center space-y-4"
      >
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-indigo-600 to-purple-600 p-0.5 mx-auto group-hover:scale-110 transition-transform shadow-lg glow-primary">
          <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center text-indigo-400">
            <UploadCloud className="w-8 h-8 animate-pulse" />
          </div>
        </div>

        <div className="space-y-1">
          <h3 className="text-base sm:text-lg font-bold text-white group-hover:text-indigo-300 transition-colors">
            Drop files here to start analyzing
          </h3>
          <p className="text-xs text-slate-400">
            PDF, DOCX, CSV, Python, JS, TXT or JSON up to 100 MB
          </p>
        </div>

        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 text-white font-semibold text-xs shadow-lg group-hover:bg-indigo-500 transition-all">
          <span>Upload Document</span>
          <ArrowRight className="w-4 h-4" />
        </div>
      </div>

      {/* Quick Starter Sample Files */}
      <div className="space-y-3">
        <div className="flex items-center justify-between text-xs">
          <span className="font-bold text-slate-300 uppercase tracking-wider">
            Or try with preloaded sample documents:
          </span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {INITIAL_FILES.map((file) => (
            <button
              key={file.id}
              onClick={() => onSelectSampleFile(file)}
              className="flex items-start gap-3 p-3.5 rounded-2xl bg-slate-900/40 hover:bg-slate-900 border border-slate-800 hover:border-indigo-500/40 text-left transition-all group"
            >
              <div className="p-2 rounded-xl bg-slate-800 group-hover:bg-indigo-500/20 text-indigo-400 transition-colors flex-shrink-0">
                {file.type === 'pdf' && <FileText className="w-4 h-4 text-rose-400" />}
                {file.type === 'docx' && <FileText className="w-4 h-4 text-blue-400" />}
                {file.type === 'code' && <FileCode className="w-4 h-4 text-emerald-400" />}
              </div>
              <div className="min-w-0 flex-1">
                <div className="text-xs font-semibold text-slate-200 group-hover:text-white truncate">
                  {file.name}
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  {file.pages} pages • {file.size}
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Prompt Suggestions Grid */}
      <div className="space-y-3 pt-2">
        <div className="text-xs font-bold text-slate-300 uppercase tracking-wider">
          Popular Q&A Prompt Templates
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {SAMPLE_PROMPT_SUGGESTIONS.map((item, idx) => (
            <button
              key={idx}
              onClick={() => onSelectPrompt(item.prompt)}
              className="group p-4 rounded-2xl bg-slate-900/40 hover:bg-slate-900 border border-slate-800 hover:border-indigo-500/40 text-left transition-all space-y-2"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs font-bold text-slate-200 group-hover:text-indigo-300">
                  {getPromptIcon(item.icon)}
                  <span>{item.title}</span>
                </div>
                <span className="px-2 py-0.5 rounded-full bg-slate-800 text-[10px] text-slate-400">
                  {item.category}
                </span>
              </div>
              <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                "{item.prompt}"
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Features Bar Footer */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-slate-800/80 text-center text-xs text-slate-400">
        <div className="flex items-center justify-center gap-2 p-2">
          <Zap className="w-4 h-4 text-amber-400" />
          <span>Sub-second Semantic Vector Search</span>
        </div>
        <div className="flex items-center justify-center gap-2 p-2">
          <Search className="w-4 h-4 text-cyan-400" />
          <span>Page & Paragraph Level Citations</span>
        </div>
        <div className="flex items-center justify-center gap-2 p-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Private Local & Vector Security</span>
        </div>
      </div>

    </div>
  );
};
