import React, { useState } from 'react';
import { 
  X, Settings, Sliders, Database, Shield, 
  Trash2, Check, Sparkles, Key
} from 'lucide-react';
import { AI_MODELS } from '../data/mockData';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onClearAllData: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  onClearAllData
}) => {
  const [activeTab, setActiveTab] = useState<'general' | 'vector' | 'api'>('general');
  const [chunkSize, setChunkSize] = useState('512');
  const [topK, setTopK] = useState('5');
  const [systemPrompt, setSystemPrompt] = useState('You are an expert Document Q&A Assistant. Always cite exact page numbers and quotes from attached files.');
  const [apiKey, setApiKey] = useState('sk-docmind-proj-••••••••••••••••');
  const [isSaved, setIsSaved] = useState(false);

  if (!isOpen) return null;

  const handleSave = () => {
    setIsSaved(true);
    setTimeout(() => {
      setIsSaved(false);
      onClose();
    }, 1000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-800 bg-slate-950/50">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <Settings className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">DocMind Preferences & RAG Settings</h2>
              <p className="text-xs text-slate-400">Configure vector retrieval, default models, and system instructions</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Buttons */}
        <div className="flex items-center gap-2 px-6 pt-4 border-b border-slate-800/80 text-xs font-semibold">
          <button
            onClick={() => setActiveTab('general')}
            className={`pb-3 px-2 border-b-2 flex items-center gap-2 transition-all ${
              activeTab === 'general'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Sliders className="w-4 h-4" /> General & AI
          </button>
          <button
            onClick={() => setActiveTab('vector')}
            className={`pb-3 px-2 border-b-2 flex items-center gap-2 transition-all ${
              activeTab === 'vector'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Database className="w-4 h-4" /> Vector Index & RAG
          </button>
          <button
            onClick={() => setActiveTab('api')}
            className={`pb-3 px-2 border-b-2 flex items-center gap-2 transition-all ${
              activeTab === 'api'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Key className="w-4 h-4" /> API Keys & Security
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-5 text-xs text-slate-300">
          
          {activeTab === 'general' && (
            <div className="space-y-4">
              <div className="space-y-1.5">
                <label className="font-bold text-slate-200">System Instruction Prompt</label>
                <textarea
                  rows={3}
                  value={systemPrompt}
                  onChange={(e) => setSystemPrompt(e.target.value)}
                  className="w-full bg-slate-950 p-3 rounded-xl border border-slate-800 text-slate-200 focus:outline-none focus:border-indigo-500"
                />
                <p className="text-[11px] text-slate-500">Guides how the AI references uploaded PDF pages and responds.</p>
              </div>

              <div className="space-y-2 pt-2 border-t border-slate-800">
                <div className="font-bold text-slate-200">Default AI Model</div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {AI_MODELS.map((m) => (
                    <div key={m.id} className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
                      <div>
                        <div className="font-bold text-slate-200">{m.name}</div>
                        <div className="text-[10px] text-slate-500">{m.contextWindow}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'vector' && (
            <div className="space-y-4">
              <div className="space-y-1.5">
                <label className="font-bold text-slate-200">Chunk Size (Tokens)</label>
                <select
                  value={chunkSize}
                  onChange={(e) => setChunkSize(e.target.value)}
                  className="w-full bg-slate-950 p-2.5 rounded-xl border border-slate-800 text-slate-200"
                >
                  <option value="256">256 tokens (High precision, shorter contexts)</option>
                  <option value="512">512 tokens (Balanced - Recommended)</option>
                  <option value="1024">1024 tokens (Longer paragraphs, broad context)</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="font-bold text-slate-200">Top-K Vector Matches</label>
                <select
                  value={topK}
                  onChange={(e) => setTopK(e.target.value)}
                  className="w-full bg-slate-950 p-2.5 rounded-xl border border-slate-800 text-slate-200"
                >
                  <option value="3">Top 3 vector chunks</option>
                  <option value="5">Top 5 vector chunks (Recommended)</option>
                  <option value="10">Top 10 vector chunks (Comprehensive review)</option>
                </select>
              </div>

              <div className="p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-300">
                <Sparkles className="w-4 h-4 inline-block mr-1 text-indigo-400" />
                DocMind utilizes BM25 + Vector Hybrid Retrieval for maximum accuracy on tables & dense text.
              </div>
            </div>
          )}

          {activeTab === 'api' && (
            <div className="space-y-4">
              <div className="space-y-1.5">
                <label className="font-bold text-slate-200">DocMind API Key</label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="w-full bg-slate-950 p-2.5 rounded-xl border border-slate-800 text-slate-200 font-mono"
                />
              </div>

              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-slate-400 space-y-1">
                <div className="font-bold text-slate-200 flex items-center gap-1.5">
                  <Shield className="w-4 h-4 text-emerald-400" /> Private Workspace Security
                </div>
                <p className="text-[11px]">Your documents are indexed in isolated local memory vector stores and are never used to train global AI models.</p>
              </div>

              <div className="pt-4 border-t border-slate-800">
                <button
                  onClick={() => {
                    if (confirm('Are you sure you want to clear all chat history and uploaded files?')) {
                      onClearAllData();
                      onClose();
                    }
                  }}
                  className="w-full flex items-center justify-center gap-2 p-2.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-300 font-medium transition-colors"
                >
                  <Trash2 className="w-4 h-4" /> Reset All Workspace Data & File Cache
                </button>
              </div>
            </div>
          )}

        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-4 border-t border-slate-800 bg-slate-950/60">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="flex items-center gap-2 px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold shadow-lg shadow-indigo-600/30 transition-all"
          >
            {isSaved ? (
              <>
                <Check className="w-4 h-4 text-emerald-400" /> Saved!
              </>
            ) : (
              'Save Changes'
            )}
          </button>
        </div>

      </div>
    </div>
  );
};
