import React, { useState, useRef, useEffect } from 'react';
import { Header } from '../components/Header';
import { ChatMessage } from '../components/ChatMessage';
import { ChatInput } from '../components/ChatInput';
import { WelcomeHero } from '../components/WelcomeHero';
import { DocumentViewerDrawer } from '../components/DocumentViewerDrawer';
import type { ChatSession, AIModel, UploadedFile, Citation } from '../types/chat';

interface ChatPageProps {
  currentSession: ChatSession | null;
  selectedModel: AIModel;
  onSelectModel: (model: AIModel) => void;
  onSendMessage: (text: string, files: UploadedFile[]) => void;
  onOpenUploadModal: () => void;
  onRegenerateResponse?: () => void;
  onClearChat?: () => void;
  onSelectSampleFile: (file: UploadedFile) => void;
  isProcessing?: boolean;
}

export const ChatPage: React.FC<ChatPageProps> = ({
  currentSession,
  selectedModel,
  onSelectModel,
  onSendMessage,
  onOpenUploadModal,
  onRegenerateResponse,
  onClearChat,
  onSelectSampleFile,
  isProcessing = false
}) => {
  const [attachedFiles, setAttachedFiles] = useState<UploadedFile[]>(currentSession?.files || []);
  const [isDocumentViewerOpen, setIsDocumentViewerOpen] = useState(false);
  const [selectedFileForViewer, setSelectedFileForViewer] = useState<UploadedFile | null>(
    currentSession?.files[0] || null
  );
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (currentSession?.files) {
      setAttachedFiles(currentSession.files);
      if (currentSession.files.length > 0) {
        setSelectedFileForViewer(currentSession.files[0]);
      }
    }
  }, [currentSession]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentSession?.messages]);

  const handleRemoveAttachedFile = (fileId: string) => {
    setAttachedFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const handleSelectCitation = (citation: Citation) => {
    setActiveCitation(citation);
    if (currentSession?.files) {
      const match = currentSession.files.find(f => f.id === citation.fileId || f.name === citation.fileName);
      if (match) {
        setSelectedFileForViewer(match);
      }
    }
    setIsDocumentViewerOpen(true);
  };

  const hasMessages = currentSession && currentSession.messages.length > 0;

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-slate-950 text-slate-100">
      
      {/* Top Bar Header */}
      <Header
        currentSession={currentSession}
        selectedModel={selectedModel}
        onSelectModel={onSelectModel}
        onOpenUploadModal={onOpenUploadModal}
        isDocumentViewerOpen={isDocumentViewerOpen}
        onToggleDocumentViewer={() => setIsDocumentViewerOpen(!isDocumentViewerOpen)}
        onClearChat={onClearChat}
      />

      {/* Center Layout: Main Chat vs Side Document Inspection Drawer */}
      <div className="flex-1 flex min-h-0 overflow-hidden relative">
        
        {/* Scrollable Chat Area */}
        <div className="flex-1 flex flex-col h-full overflow-y-auto">
          {!hasMessages ? (
            <div className="flex-1 flex items-center justify-center py-6">
              <WelcomeHero
                onOpenUploadModal={onOpenUploadModal}
                onSelectPrompt={(prompt) => onSendMessage(prompt, attachedFiles)}
                onSelectSampleFile={(file) => {
                  onSelectSampleFile(file);
                  setAttachedFiles([file]);
                }}
              />
            </div>
          ) : (
            <div className="flex-1 space-y-2 pb-6">
              {currentSession.messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  message={message}
                  onRegenerate={onRegenerateResponse}
                  onSelectCitation={handleSelectCitation}
                />
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}

          {/* Floating Chat Input Bar */}
          <ChatInput
            onSendMessage={(text, files) => {
              onSendMessage(text, files);
            }}
            attachedFiles={attachedFiles}
            onRemoveAttachedFile={handleRemoveAttachedFile}
            onOpenUploadModal={onOpenUploadModal}
            isProcessing={isProcessing}
          />
        </div>

        {/* Side-by-side Document Viewer Drawer */}
        <DocumentViewerDrawer
          isOpen={isDocumentViewerOpen}
          onClose={() => setIsDocumentViewerOpen(false)}
          file={selectedFileForViewer || (currentSession?.files[0] || null)}
          activeCitation={activeCitation}
        />

      </div>
    </div>
  );
};
