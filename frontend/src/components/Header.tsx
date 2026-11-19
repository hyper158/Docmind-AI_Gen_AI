import React, { useState } from 'react';
import { 
  Sparkles, ChevronDown, UploadCloud, PanelRightOpen, 
  PanelRightClose, FileText, Share2, MoreVertical,
  Cpu, Zap, Brain, Check
} from 'lucide-react';
import type { ChatSession, AIModel } from '../types/chat';
import { AI_MODELS } from '../data/mockData';

interface HeaderProps {
  currentSession: ChatSession | null;
  selectedModel: AIModel;
  onSelectModel: (model: AIModel) => void;
  onOpenUploadModal: () => void;
  isDocumentViewerOpen: boolean;
  onToggleDocumentViewer: () => void;
  onClearChat?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentSession,
  selectedModel,
  onSelectModel,
  onOpenUploadModal,
  isDocumentViewerOpen,
  onToggleDocumentViewer,
  onClearChat
}) => {
  const [isModelDropdownOpen, setIsModelDropdownOpen] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const getModelIcon = (iconName: string) => {
    switch (iconName) {
      case 'Cpu': return <Cpu className="w-4 h-4 text-purple-400" />;
      case 'Zap': return <Zap className="w-4 h-4 text-amber-400" />;
      case 'Brain': return <Brain className="w-4 h-4 text-emerald-400" />;
      default: return <Sparkles className="w-4 h-4 text-indigo-400" />;
    }
  };

  const attachedFilesCount = currentSession?.files.length || 0;

  return (
    <header className="sticky top-0 z-20 flex items-center justify-between px-4 sm:px-6 py-3 bg-slate-950/80 backdrop-blur-xl border-b border-slate-800/70 text-slate-200">
      {/* Left: Chat Title & Model Selector */}
      <div className="flex items-center gap-3 min-w-0">
        <div className="relative">
          <button
            onClick={() => setIsModelDropdownOpen(!isModelDropdownOpen)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-indigo-500/50 text-xs font-semibold text-white transition-all shadow-sm"
          >
            {getModelIcon(selectedModel.iconName)}
            <span className="truncate">{selectedModel.name}</span>
            {selectedModel.badge && (
              <span className="hidden sm:inline px-1.5 py-0.2 text-[10px] rounded bg-indigo-500/20 text-indigo-300 font-bold border border-indigo-500/30">
                {selectedModel.badge}
              </span>
            )}
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          </button>

          {/* Model Selector Dropdown */}
          {isModelDropdownOpen && (
            <div 
              className="absolute left-0 top-full mt-2 w-72 sm:w-80 rounded-2xl bg-slate-900 border border-slate-700/80 shadow-2xl p-2 z-50 animate-in fade-in zoom-in-95 duration-150"
              onMouseLeave={() => setIsModelDropdownOpen(false)}
            >
              <div className="px-3 py-2 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                Select Intelligence Engine
              </div>
              <div className="space-y-1">
                {AI_MODELS.map((model) => (
                  <button
                    key={model.id}
                    onClick={() => {
                      onSelectModel(model);
                      setIsModelDropdownOpen(false);
                    }}
                    className={`w-full flex items-start gap-3 p-2.5 rounded-xl text-left transition-all ${
                      selectedModel.id === model.id
                        ? 'bg-indigo-600/20 border border-indigo-500/40 text-white'
                        : 'hover:bg-slate-800/80 text-slate-300'
                    }`}
                  >
                    <div className="mt-0.5 p-1.5 rounded-lg bg-slate-800 border border-white/5">
                      {getModelIcon(model.iconName)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-100">{model.name}</span>
                        {selectedModel.id === model.id && (
                          <Check className="w-3.5 h-3.5 text-indigo-400" />
                        )}
                      </div>
                      <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-2">{model.description}</p>
                      <div className="flex items-center gap-2 mt-1 text-[10px] text-slate-400">
                        <span>{model.contextWindow}</span>
                        <span>•</span>
                        <span className="text-emerald-400">{model.speed}</span>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="h-4 w-px bg-slate-800 hidden sm:block" />

        {/* Current Active Chat Title */}
        <div className="hidden sm:flex items-center gap-2 min-w-0">
          <h1 className="text-sm font-semibold text-slate-200 truncate max-w-[200px] lg:max-w-[350px]">
            {currentSession ? currentSession.title : 'New Document Q&A'}
          </h1>
        </div>
      </div>

      {/* Right Action Controls */}
      <div className="flex items-center gap-2">
        {/* Attached files counter & quick viewer toggle */}
        {attachedFilesCount > 0 && (
          <button
            onClick={onToggleDocumentViewer}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium border transition-all ${
              isDocumentViewerOpen 
                ? 'bg-indigo-600/20 border-indigo-500/50 text-indigo-300' 
                : 'bg-slate-900 border-slate-800 hover:border-slate-700 text-slate-300'
            }`}
            title="Toggle Split-Screen Document Viewer"
          >
            <FileText className="w-4 h-4 text-indigo-400" />
            <span className="hidden sm:inline">Inspect Files</span>
            <span className="px-1.5 py-0.2 rounded-full bg-indigo-500/20 text-indigo-300 text-[10px] font-bold">
              {attachedFilesCount}
            </span>
            {isDocumentViewerOpen ? <PanelRightClose className="w-3.5 h-3.5 ml-0.5" /> : <PanelRightOpen className="w-3.5 h-3.5 ml-0.5" />}
          </button>
        )}

        {/* Upload File trigger button */}
        <button
          onClick={onOpenUploadModal}
          className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-indigo-600/10 hover:bg-indigo-600/20 border border-indigo-500/30 text-indigo-300 font-medium text-xs transition-all shadow-sm active:scale-95"
        >
          <UploadCloud className="w-4 h-4 text-indigo-400" />
          <span className="hidden sm:inline">Upload File</span>
        </button>

        {/* More Actions Menu */}
        <div className="relative">
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <MoreVertical className="w-4 h-4" />
          </button>

          {isMenuOpen && (
            <div 
              className="absolute right-0 top-full mt-2 w-48 rounded-xl bg-slate-900 border border-slate-800 shadow-xl p-1 z-50 text-xs"
              onMouseLeave={() => setIsMenuOpen(false)}
            >
              <button 
                onClick={() => {
                  alert('Chat link copied to clipboard!');
                  setIsMenuOpen(false);
                }}
                className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
              >
                <Share2 className="w-3.5 h-3.5" /> Share Chat Session
              </button>
              {onClearChat && (
                <button 
                  onClick={() => {
                    onClearChat();
                    setIsMenuOpen(false);
                  }}
                  className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-rose-400 hover:bg-rose-500/10 transition-colors"
                >
                  Clear Chat History
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
