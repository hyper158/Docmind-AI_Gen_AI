import { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { FileUploadModal } from './components/FileUploadModal';
import { SettingsModal } from './components/SettingsModal';
import { ChatPage } from './pages/ChatPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import type { ChatSession, AIModel, UploadedFile, ChatMessage } from './types/chat';
import { AI_MODELS } from './data/mockData';
import { api, mapBackendCitation } from './services/api';

export function App() {
  const [activeTab, setActiveTab] = useState<'chat' | 'documents' | 'analytics'>('chat');
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string>('');
  const [allFiles, setAllFiles] = useState<UploadedFile[]>([]);
  const [selectedModel, setSelectedModel] = useState<AIModel>(AI_MODELS[0]);
  const [isAiResponding, setIsAiResponding] = useState<boolean>(false);
  
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState<boolean>(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState<boolean>(false);
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState<boolean>(false);

  // Fetch initial documents and sessions from backend on startup
  useEffect(() => {
    async function loadInitialData() {
      try {
        const [fetchedDocs, fetchedSessions] = await Promise.all([
          api.getDocuments().catch(() => []),
          api.getSessions().catch(() => []),
        ]);

        setAllFiles(fetchedDocs);

        if (fetchedSessions.length > 0) {
          setSessions(fetchedSessions);
          setActiveSessionId(fetchedSessions[0].id);
        } else {
          // Initialize a clean starting session
          try {
            const initialSess = await api.createSession('New Syllabus Q&A Session');
            setSessions([initialSess]);
            setActiveSessionId(initialSess.id);
          } catch {
            const fallbackSess: ChatSession = {
              id: `session-local-1`,
              title: 'New Syllabus Q&A Session',
              updatedAt: 'Just now',
              files: [],
              messages: [],
              model: selectedModel.id,
            };
            setSessions([fallbackSess]);
            setActiveSessionId(fallbackSess.id);
          }
        }
      } catch (err) {
        console.error('Error initializing data from backend:', err);
      }
    }

    loadInitialData();
  }, []);

  const activeSession = sessions.find(s => s.id === activeSessionId) || (sessions[0] || null);

  // Handler: New Chat
  const handleNewChat = async () => {
    try {
      const created = await api.createSession('New Syllabus Q&A Session');
      setSessions(prev => [created, ...prev]);
      setActiveSessionId(created.id);
    } catch {
      const newId = `session-${Date.now()}`;
      const newSession: ChatSession = {
        id: newId,
        title: 'New Syllabus Q&A Session',
        updatedAt: 'Just now',
        pinned: false,
        model: selectedModel.id,
        files: [],
        messages: []
      };
      setSessions(prev => [newSession, ...prev]);
      setActiveSessionId(newId);
    }
    setActiveTab('chat');
  };

  // Handler: Delete Session
  const handleDeleteSession = async (id: string) => {
    try {
      await api.deleteSession(id);
    } catch (err) {
      console.warn('Backend delete session failed:', err);
    }
    const updated = sessions.filter(s => s.id !== id);
    setSessions(updated);
    if (activeSessionId === id && updated.length > 0) {
      setActiveSessionId(updated[0].id);
    }
  };

  // Handler: Upload Complete
  const handleUploadComplete = (newFiles: UploadedFile[]) => {
    setAllFiles(prev => {
      const existingIds = new Set(prev.map(f => f.id));
      const fresh = newFiles.filter(f => !existingIds.has(f.id));
      return [...fresh, ...prev];
    });

    // Attach uploaded files to current active session
    if (activeSessionId) {
      setSessions(prev =>
        prev.map(s => {
          if (s.id === activeSessionId) {
            const combinedFiles = [...s.files, ...newFiles.filter(nf => !s.files.some(sf => sf.id === nf.id))];
            const updatedTitle = s.messages.length === 0 
              ? `QA: ${newFiles[0].name}` 
              : s.title;
            return {
              ...s,
              files: combinedFiles,
              title: updatedTitle
            };
          }
          return s;
        })
      );
    }
  };

  // Handler: Send Message in Chat
  const handleSendMessage = async (text: string, attachedFiles: UploadedFile[]) => {
    if (!activeSessionId) return;

    const userMessage: ChatMessage = {
      id: `msg-user-${Date.now()}`,
      sender: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      attachedFiles
    };

    // Update session title if first message
    const currentSess = sessions.find(s => s.id === activeSessionId);
    let sessionTitle = currentSess?.title || 'New Chat';
    if (currentSess && currentSess.messages.length === 0) {
      sessionTitle = text.slice(0, 32) + (text.length > 32 ? '...' : '');
    }

    // Append user message immediately
    setSessions(prev =>
      prev.map(s => {
        if (s.id === activeSessionId) {
          return {
            ...s,
            title: sessionTitle,
            files: attachedFiles.length > 0 ? attachedFiles : s.files,
            messages: [...s.messages, userMessage]
          };
        }
        return s;
      })
    );

    setIsAiResponding(true);

    try {
      // Fallback hierarchy for document scope:
      // 1. Attached files in ChatInput
      // 2. Files attached to current session
      // 3. All uploaded files in the workspace
      const sessionFiles = sessions.find(s => s.id === activeSessionId)?.files || [];
      const resolvedFiles = attachedFiles.length > 0 
        ? attachedFiles 
        : (sessionFiles.length > 0 ? sessionFiles : allFiles);
      const selectedDocIds = resolvedFiles.map(f => f.id);

      const res = await api.sendMessage({
        question: text,
        sessionId: activeSessionId,
        selectedDocumentIds: selectedDocIds,
      });

      const aiResponse: ChatMessage = {
        id: res.message_id || `msg-ai-${Date.now()}`,
        sender: 'assistant',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        reasoningTime: res.reasoning_time || 1.2,
        thinkingProcess: res.thinking_process || `Retrieved ${res.retrieved_source_count} chunks from syllabus index.`,
        content: res.answer,
        citations: res.citations.map(mapBackendCitation),
      };

      setSessions(prev =>
        prev.map(s => {
          if (s.id === activeSessionId) {
            return {
              ...s,
              messages: [...s.messages, aiResponse]
            };
          }
          return s;
        })
      );
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to get answer from DocMind backend.';
      const errorResponse: ChatMessage = {
        id: `msg-error-${Date.now()}`,
        sender: 'assistant',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        content: `⚠️ **Error**: ${errorMessage}\n\nPlease verify that the Python backend is running on \`http://localhost:8000\` and that your syllabus PDF is uploaded.`,
      };

      setSessions(prev =>
        prev.map(s => {
          if (s.id === activeSessionId) {
            return {
              ...s,
              messages: [...s.messages, errorResponse]
            };
          }
          return s;
        })
      );
    } finally {
      setIsAiResponding(false);
    }
  };

  // Handler: Select Sample File for quick Q&A
  const handleSelectSampleFile = (file: UploadedFile) => {
    handleNewChat();
    setTimeout(() => {
      handleUploadComplete([file]);
    }, 100);
  };

  // Handler: Clear current chat history
  const handleClearChat = () => {
    if (activeSessionId) {
      setSessions(prev =>
        prev.map(s => s.id === activeSessionId ? { ...s, messages: [] } : s)
      );
    }
  };

  // Handler: Delete File
  const handleDeleteFile = async (fileId: string) => {
    try {
      await api.deleteDocument(fileId);
    } catch (err) {
      console.warn('Backend delete document failed:', err);
    }
    setAllFiles(prev => prev.filter(f => f.id !== fileId));
    setSessions(prev =>
      prev.map(s => ({
        ...s,
        files: s.files.filter(f => f.id !== fileId)
      }))
    );
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 selection:bg-indigo-500 selection:text-white font-sans">
      
      {/* Sidebar Navigation */}
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={setActiveSessionId}
        onNewChat={handleNewChat}
        onDeleteSession={handleDeleteSession}
        activeTab={activeTab}
        onChangeTab={setActiveTab}
        onOpenSettings={() => setIsSettingsModalOpen(true)}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
      />

      {/* Main Viewport Content Area */}
      <main className="flex-1 flex flex-col h-full min-w-0 overflow-hidden relative">
        {activeTab === 'chat' && (
          <ChatPage
            currentSession={activeSession}
            selectedModel={selectedModel}
            onSelectModel={setSelectedModel}
            onSendMessage={handleSendMessage}
            onOpenUploadModal={() => setIsUploadModalOpen(true)}
            onRegenerateResponse={() => {
              if (activeSession && activeSession.messages.length > 0) {
                const lastUserMsg = [...activeSession.messages].reverse().find(m => m.sender === 'user');
                if (lastUserMsg) {
                  handleSendMessage(lastUserMsg.content, lastUserMsg.attachedFiles || []);
                }
              }
            }}
            onClearChat={handleClearChat}
            onSelectSampleFile={handleSelectSampleFile}
            isProcessing={isAiResponding}
          />
        )}

        {activeTab === 'documents' && (
          <DocumentsPage
            files={allFiles}
            onOpenUploadModal={() => setIsUploadModalOpen(true)}
            onSelectFileForChat={(file) => {
              handleSelectSampleFile(file);
              setActiveTab('chat');
            }}
            onDeleteFile={handleDeleteFile}
          />
        )}

        {activeTab === 'analytics' && (
          <AnalyticsPage />
        )}
      </main>

      {/* Upload File Modal */}
      <FileUploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onUploadComplete={handleUploadComplete}
      />

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsModalOpen}
        onClose={() => setIsSettingsModalOpen(false)}
        onClearAllData={() => {
          setSessions([]);
          setAllFiles([]);
          handleNewChat();
        }}
      />

    </div>
  );
}

export default App;
