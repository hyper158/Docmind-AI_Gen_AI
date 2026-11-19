import React, { useState } from 'react';
import { 
  Plus, MessageSquare, FolderKanban, BarChart3, Search, 
  Settings, ChevronLeft, ChevronRight, Sparkles, Pin, 
  Trash2, HardDrive, Check, Layers
} from 'lucide-react';
import type { ChatSession } from '../types/chat';

interface SidebarProps {
  sessions: ChatSession[];
  activeSessionId: string;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  onDeleteSession: (id: string) => void;
  activeTab: 'chat' | 'documents' | 'analytics';
  onChangeTab: (tab: 'chat' | 'documents' | 'analytics') => void;
  onOpenSettings: () => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  onDeleteSession,
  activeTab,
  onChangeTab,
  onOpenSettings,
  isCollapsed,
  onToggleCollapse
}) => {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredSessions = sessions.filter(s => 
    s.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.files.some(f => f.name.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const pinnedSessions = filteredSessions.filter(s => s.pinned);
  const recentSessions = filteredSessions.filter(s => !s.pinned);

  return (
    <aside 
      className={`relative flex flex-col h-full bg-slate-950/90 backdrop-blur-xl border-r border-slate-800/80 text-slate-300 transition-all duration-300 z-30 ${
        isCollapsed ? 'w-20' : 'w-72 sm:w-80'
      }`}
    >
      {/* Sidebar Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-800/60">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-cyan-400 p-0.5 flex-shrink-0 glow-primary shadow-lg">
            <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-indigo-400 animate-pulse" />
            </div>
          </div>

          {!isCollapsed && (
            <div className="flex flex-col min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-base text-white tracking-wide truncate">DocMind</span>
                <span className="text-[10px] font-extrabold px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 uppercase tracking-widest">
                  AI
                </span>
              </div>
              <span className="text-[11px] text-slate-400 truncate">Multi-File Intelligence</span>
            </div>
          )}
        </div>

        {/* Collapse toggle button */}
        <button 
          onClick={onToggleCollapse}
          className="hidden md:flex p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/80 transition-colors"
          title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* New Chat Button */}
      <div className="p-3">
        <button
          onClick={onNewChat}
          className={`w-full flex items-center justify-center gap-2.5 py-3 px-4 rounded-xl bg-gradient-to-r from-indigo-600 via-purple-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-white font-medium shadow-lg shadow-indigo-600/25 border border-indigo-400/30 transition-all duration-200 active:scale-[0.98] ${
            isCollapsed ? 'px-0 justify-center' : ''
          }`}
          title="Start new Q&A chat"
        >
          <Plus className="w-5 h-5" />
          {!isCollapsed && <span>New File Chat</span>}
        </button>
      </div>

      {/* Navigation Tabs */}
      <div className="px-3 py-1 flex flex-col gap-1 border-b border-slate-800/50">
        <button
          onClick={() => onChangeTab('chat')}
          className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
            activeTab === 'chat' 
              ? 'bg-slate-800/90 text-indigo-400 border border-indigo-500/20' 
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
          }`}
        >
          <MessageSquare className="w-4 h-4" />
          {!isCollapsed && <span>Chat Workspace</span>}
        </button>

        <button
          onClick={() => onChangeTab('documents')}
          className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
            activeTab === 'documents' 
              ? 'bg-slate-800/90 text-indigo-400 border border-indigo-500/20' 
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
          }`}
        >
          <FolderKanban className="w-4 h-4" />
          {!isCollapsed && <span>Document Library</span>}
        </button>

        <button
          onClick={() => onChangeTab('analytics')}
          className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
            activeTab === 'analytics' 
              ? 'bg-slate-800/90 text-indigo-400 border border-indigo-500/20' 
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
          }`}
        >
          <BarChart3 className="w-4 h-4" />
          {!isCollapsed && <span>Insights & Analytics</span>}
        </button>
      </div>

      {/* Chat History Section */}
      {!isCollapsed && (
        <div className="flex-1 overflow-y-auto px-3 py-3 space-y-4">
          {/* Search box */}
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Search chats or files..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-900/80 text-xs text-slate-200 placeholder-slate-500 rounded-xl pl-9 pr-3 py-2 border border-slate-800 focus:outline-none focus:border-indigo-500/50 transition-colors"
            />
          </div>

          {/* Pinned section */}
          {pinnedSessions.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 px-2 mb-1.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                <Pin className="w-3 h-3 text-amber-400" />
                <span>Pinned Chats</span>
              </div>
              <div className="space-y-1">
                {pinnedSessions.map((session) => (
                  <div
                    key={session.id}
                    onClick={() => {
                      onSelectSession(session.id);
                      onChangeTab('chat');
                    }}
                    className={`group relative flex items-center justify-between p-2.5 rounded-xl text-xs cursor-pointer transition-all ${
                      activeSessionId === session.id && activeTab === 'chat'
                        ? 'bg-slate-800/90 text-white font-medium border border-indigo-500/30'
                        : 'text-slate-300 hover:bg-slate-900/70 hover:text-white'
                    }`}
                  >
                    <div className="flex items-center gap-2.5 min-w-0 pr-6">
                      <MessageSquare className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
                      <span className="truncate">{session.title}</span>
                    </div>

                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteSession(session.id);
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-rose-400 transition-opacity"
                      title="Delete chat"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recent section */}
          <div>
            <div className="px-2 mb-1.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Recent Sessions ({recentSessions.length})
            </div>
            {recentSessions.length === 0 ? (
              <p className="text-xs text-slate-500 px-2 italic">No chats found</p>
            ) : (
              <div className="space-y-1">
                {recentSessions.map((session) => (
                  <div
                    key={session.id}
                    onClick={() => {
                      onSelectSession(session.id);
                      onChangeTab('chat');
                    }}
                    className={`group relative flex items-center justify-between p-2.5 rounded-xl text-xs cursor-pointer transition-all ${
                      activeSessionId === session.id && activeTab === 'chat'
                        ? 'bg-slate-800/90 text-white font-medium border border-indigo-500/30'
                        : 'text-slate-400 hover:bg-slate-900/70 hover:text-white'
                    }`}
                  >
                    <div className="flex items-center gap-2.5 min-w-0 pr-4">
                      <Layers className="w-3.5 h-3.5 text-slate-500 group-hover:text-indigo-400 flex-shrink-0 transition-colors" />
                      <div className="flex flex-col min-w-0">
                        <span className="truncate text-slate-200 group-hover:text-white">{session.title}</span>
                        {session.files.length > 0 && (
                          <span className="text-[10px] text-slate-500 truncate">
                            📎 {session.files[0].name} {session.files.length > 1 ? `+${session.files.length - 1}` : ''}
                          </span>
                        )}
                      </div>
                    </div>

                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteSession(session.id);
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-rose-400 transition-opacity"
                      title="Delete chat"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Collapsed spacer */}
      {isCollapsed && <div className="flex-1" />}

      {/* Footer User & Storage Card */}
      <div className="p-3 border-t border-slate-800/60 space-y-2">
        {!isCollapsed && (
          <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-slate-400 flex items-center gap-1.5">
                <HardDrive className="w-3.5 h-3.5 text-cyan-400" /> Vector Index
              </span>
              <span className="text-slate-300 font-semibold">6.3 MB / 50 MB</span>
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div className="bg-gradient-to-r from-cyan-500 to-indigo-500 h-full w-[13%]" />
            </div>
          </div>
        )}

        <div className="flex items-center justify-between gap-2 pt-1">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 flex items-center justify-center text-white font-bold text-xs ring-2 ring-indigo-500/30">
              AY
            </div>
            {!isCollapsed && (
              <div className="flex flex-col min-w-0">
                <span className="text-xs font-semibold text-slate-200 truncate">Ayush Pro</span>
                <span className="text-[10px] text-emerald-400 flex items-center gap-1">
                  <Check className="w-2.5 h-2.5" /> Unlimited Documents
                </span>
              </div>
            )}
          </div>

          <button
            onClick={onOpenSettings}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            title="Settings"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
};
