import React, { useState, useRef, useEffect } from 'react';
import { 
  Paperclip, Mic, X, FileText, ArrowUp
} from 'lucide-react';
import type { UploadedFile } from '../types/chat';

interface ChatInputProps {
  onSendMessage: (messageText: string, attachedFiles: UploadedFile[]) => void;
  attachedFiles: UploadedFile[];
  onRemoveAttachedFile: (fileId: string) => void;
  onOpenUploadModal: () => void;
  isProcessing?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  attachedFiles,
  onRemoveAttachedFile,
  onOpenUploadModal,
  isProcessing = false
}) => {
  const [inputText, setInputText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea up to max height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  }, [inputText]);

  const handleSend = () => {
    if (!inputText.trim() && attachedFiles.length === 0) return;
    onSendMessage(inputText.trim(), attachedFiles);
    setInputText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4 pb-4 sm:pb-6">
      
      {/* Floating Main Box Container */}
      <div className="relative rounded-3xl glass-panel border border-slate-700/60 shadow-2xl p-3 sm:p-4 space-y-3 transition-all duration-200 focus-within:border-indigo-500/60 focus-within:ring-2 focus-within:ring-indigo-500/20">
        
        {/* Attached Files Active Chips */}
        {attachedFiles.length > 0 && (
          <div className="flex flex-wrap gap-2 pb-2 border-b border-slate-800/80">
            {attachedFiles.map(file => (
              <div 
                key={file.id} 
                className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-700 text-xs font-medium text-slate-200 animate-in fade-in zoom-in-95 duration-150"
              >
                <FileText className="w-3.5 h-3.5 text-indigo-400" />
                <span className="max-w-[150px] truncate">{file.name}</span>
                <button
                  onClick={() => onRemoveAttachedFile(file.id)}
                  className="text-slate-400 hover:text-rose-400 transition-colors p-0.5 rounded-md hover:bg-slate-800"
                  title="Remove attachment"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Text Input Area */}
        <div className="relative flex items-start gap-3">
          <textarea
            ref={textareaRef}
            rows={1}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              attachedFiles.length > 0 
                ? `Ask anything about ${attachedFiles[0].name}...`
                : "Ask a question, upload a document, or request a summary..."
            }
            className="w-full bg-transparent text-slate-100 placeholder-slate-500 text-sm focus:outline-none resize-none min-h-[44px] py-2 px-1 leading-relaxed"
          />
        </div>

        {/* Bottom Toolbar & Action Controls */}
        <div className="flex items-center justify-between pt-1 text-xs">
          
          {/* Left Action Buttons: File Picker & Voice */}
          <div className="flex items-center gap-1.5">
            <button
              onClick={onOpenUploadModal}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 font-medium transition-all hover:border-slate-700 active:scale-95"
              title="Attach Document or Code File"
            >
              <Paperclip className="w-4 h-4 text-indigo-400" />
              <span className="hidden sm:inline">Attach File</span>
            </button>

            <button
              onClick={() => setIsRecording(!isRecording)}
              className={`p-2 rounded-xl border transition-all ${
                isRecording 
                  ? 'bg-rose-500/20 border-rose-500/40 text-rose-400 animate-pulse' 
                  : 'bg-slate-900/80 hover:bg-slate-800 border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
              title="Voice Dictation"
            >
              <Mic className="w-4 h-4" />
            </button>
          </div>

          {/* Right Action Buttons: Character counter & Send Button */}
          <div className="flex items-center gap-3">
            <span className="text-[11px] text-slate-500 hidden sm:inline">
              {inputText.length} / 4000 chars
            </span>

            <button
              onClick={handleSend}
              disabled={(!inputText.trim() && attachedFiles.length === 0) || isProcessing}
              className={`flex items-center justify-center w-10 h-10 rounded-2xl transition-all duration-200 shadow-lg ${
                inputText.trim() || attachedFiles.length > 0
                  ? 'bg-gradient-to-r from-indigo-600 via-purple-600 to-indigo-700 text-white hover:brightness-110 active:scale-95 glow-primary'
                  : 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700/50'
              }`}
              title="Send Message"
            >
              <ArrowUp className="w-5 h-5 stroke-[2.5]" />
            </button>
          </div>

        </div>

      </div>

      {/* Footer Instructions / AI Disclaimer */}
      <div className="text-center mt-2">
        <span className="text-[11px] text-slate-500">
          DocMind references exact document pages & vector embeddings. Verify critical facts.
        </span>
      </div>
    </div>
  );
};
