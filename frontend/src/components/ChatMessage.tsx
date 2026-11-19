import React, { useState } from 'react';
import { 
  Sparkles, Copy, Check, ThumbsUp, ThumbsDown, 
  RotateCcw, ChevronDown, ChevronUp, FileText, 
  ExternalLink, Volume2, User
} from 'lucide-react';
import type { ChatMessage as ChatMessageType, Citation } from '../types/chat';
import { FileBadge } from './FileBadge';

interface ChatMessageProps {
  message: ChatMessageType;
  onRegenerate?: () => void;
  onSelectCitation?: (citation: Citation) => void;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  onRegenerate,
  onSelectCitation
}) => {
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState<'like' | 'dislike' | null>(message.feedback || null);
  const [showThinking, setShowThinking] = useState(false);

  const isUser = message.sender === 'user';

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Markdown Renderer Simulation
  const renderFormattedContent = (text: string) => {
    if (!text || !text.trim()) {
      return (
        <p className="text-slate-400 italic text-sm">
          Generating response from your syllabus documents...
        </p>
      );
    }

    const lines = text.split('\n');
    
    return (
      <div className="space-y-3 text-sm leading-relaxed">
        {lines.map((line, idx) => {
          if (line.startsWith('# ')) {
            return (
              <h1 key={idx} className="text-xl font-bold text-white mt-4 mb-2">
                {line.replace('# ', '')}
              </h1>
            );
          }
          if (line.startsWith('## ')) {
            return (
              <h2 key={idx} className="text-lg font-extrabold text-indigo-300 mt-5 mb-2">
                {line.replace('## ', '')}
              </h2>
            );
          }
          if (line.startsWith('### ')) {
            return (
              <h3 key={idx} className="text-base font-bold text-white mt-4 mb-2 flex items-center gap-2">
                {line.replace('### ', '')}
              </h3>
            );
          }
          if (line.startsWith('- ') || line.startsWith('* ')) {
            const content = line.substring(2);
            return (
              <div key={idx} className="flex items-start gap-2 ml-2">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-2 flex-shrink-0" />
                <span className="text-slate-200">{formatInlineFormatting(content)}</span>
              </div>
            );
          }
          if (/^\d+\.\s/.test(line)) {
            const match = line.match(/^(\d+)\.\s(.*)/);
            if (match) {
              return (
                <div key={idx} className="flex items-start gap-2 ml-2">
                  <span className="font-semibold text-indigo-400 min-w-[18px]">{match[1]}.</span>
                  <span className="text-slate-200">{formatInlineFormatting(match[2])}</span>
                </div>
              );
            }
          }
          if (line.startsWith('> ')) {
            return (
              <blockquote key={idx} className="border-l-4 border-indigo-500 pl-4 py-1.5 my-2 bg-indigo-500/10 rounded-r-xl text-indigo-200 font-medium italic">
                {formatInlineFormatting(line.replace('> ', ''))}
              </blockquote>
            );
          }
          if (line === '---') {
            return <hr key={idx} className="border-slate-800 my-4" />;
          }
          if (line.trim() === '') {
            return <div key={idx} className="h-1" />;
          }

          return (
            <p key={idx} className="text-slate-200">
              {formatInlineFormatting(line)}
            </p>
          );
        })}
      </div>
    );
  };

  const formatInlineFormatting = (text: string) => {
    // Process bold (**text**) and code (`text`) tokens
    const parts = text.split(/(\*\*.*?\*\*|`.*?`)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} className="font-semibold text-white">{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return (
          <code key={i} className="px-1.5 py-0.5 rounded bg-slate-800 text-indigo-300 font-mono text-xs border border-slate-700/60">
            {part.slice(1, -1)}
          </code>
        );
      }
      return part;
    });
  };

  return (
    <div className={`py-6 px-4 sm:px-6 transition-colors ${
      isUser ? 'bg-transparent' : 'bg-slate-900/40 border-y border-slate-800/40'
    }`}>
      <div className="max-w-4xl mx-auto flex items-start gap-4">
        
        {/* Avatar */}
        <div className="flex-shrink-0 mt-0.5">
          {isUser ? (
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-xs shadow-md">
              <User className="w-4 h-4" />
            </div>
          ) : (
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-cyan-400 p-0.5 shadow-lg glow-primary">
              <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-indigo-400" />
              </div>
            </div>
          )}
        </div>

        {/* Message Container */}
        <div className="flex-1 min-w-0 space-y-3">
          
          {/* Top Info Bar */}
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="font-bold text-slate-300">
              {isUser ? 'You' : 'DocMind AI'}
            </span>
            <span className="text-[11px] text-slate-500">{message.timestamp}</span>
          </div>

          {/* User Attached Files Badges */}
          {message.attachedFiles && message.attachedFiles.length > 0 && (
            <div className="flex flex-wrap gap-2 pt-1">
              {message.attachedFiles.map(file => (
                <FileBadge key={file.id} file={file} compact />
              ))}
            </div>
          )}

          {/* AI Thinking Process Accordion (Claude/Reasoning model style) */}
          {!isUser && message.thinkingProcess && (
            <div className="rounded-xl border border-slate-800 bg-slate-950/60 overflow-hidden text-xs">
              <button
                onClick={() => setShowThinking(!showThinking)}
                className="w-full flex items-center justify-between px-3 py-2 text-slate-400 hover:text-slate-200 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-400 animate-spin" />
                  <span>Thought for {message.reasoningTime || 1.5} seconds</span>
                </div>
                {showThinking ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              </button>
              {showThinking && (
                <div className="px-3 py-2.5 border-t border-slate-800/80 bg-slate-900/50 text-slate-400 text-xs font-mono leading-relaxed">
                  {message.thinkingProcess}
                </div>
              )}
            </div>
          )}

          {/* Message Body Content */}
          <div className="prose prose-invert max-w-none">
            {renderFormattedContent(message.content)}
          </div>

          {/* Document Citations & Sources (Unique to Document Q&A AI) */}
          {!isUser && message.citations && message.citations.length > 0 && (
            <div className="mt-4 pt-4 border-t border-slate-800/80 space-y-2">
              <div className="text-xs font-bold text-indigo-300 flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-indigo-400" />
                Verified Document Citations ({message.citations.length})
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {message.citations.map((citation) => (
                  <button
                    key={citation.id}
                    onClick={() => onSelectCitation && onSelectCitation(citation)}
                    className="flex items-start gap-2.5 p-2.5 rounded-xl bg-slate-950/70 hover:bg-slate-900 border border-slate-800 hover:border-indigo-500/40 text-left transition-all group"
                  >
                    <div className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400 flex-shrink-0 mt-0.5">
                      <FileText className="w-3.5 h-3.5" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between text-[11px] font-semibold text-slate-200">
                        <span className="truncate">{citation.fileName}</span>
                        {citation.pageNumber && (
                          <span className="px-1.5 py-0.2 rounded bg-indigo-500/20 text-indigo-300 text-[10px]">
                            Page {citation.pageNumber}
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-400 mt-1 line-clamp-2 italic">
                        "{citation.snippet}"
                      </p>
                    </div>
                    <ExternalLink className="w-3.5 h-3.5 text-slate-500 group-hover:text-indigo-400 transition-colors flex-shrink-0 mt-0.5" />
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Assistant Action Buttons Toolbar */}
          {!isUser && (
            <div className="flex items-center gap-2 pt-2 text-xs text-slate-400">
              <button
                onClick={handleCopy}
                className="flex items-center gap-1 px-2.5 py-1 rounded-lg hover:bg-slate-800 hover:text-white transition-colors"
                title="Copy response"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Copied!' : 'Copy'}</span>
              </button>

              {onRegenerate && (
                <button
                  onClick={onRegenerate}
                  className="flex items-center gap-1 px-2.5 py-1 rounded-lg hover:bg-slate-800 hover:text-white transition-colors"
                  title="Regenerate answer"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Regenerate</span>
                </button>
              )}

              <div className="h-3 w-px bg-slate-800 mx-1" />

              <button
                onClick={() => setFeedback(feedback === 'like' ? null : 'like')}
                className={`p-1.5 rounded-lg hover:bg-slate-800 transition-colors ${
                  feedback === 'like' ? 'text-emerald-400 bg-emerald-500/10' : 'hover:text-white'
                }`}
                title="Good response"
              >
                <ThumbsUp className="w-3.5 h-3.5" />
              </button>

              <button
                onClick={() => setFeedback(feedback === 'dislike' ? null : 'dislike')}
                className={`p-1.5 rounded-lg hover:bg-slate-800 transition-colors ${
                  feedback === 'dislike' ? 'text-rose-400 bg-rose-500/10' : 'hover:text-white'
                }`}
                title="Poor response"
              >
                <ThumbsDown className="w-3.5 h-3.5" />
              </button>

              <button
                onClick={() => alert('Reading text aloud...')}
                className="p-1.5 rounded-lg hover:bg-slate-800 hover:text-white transition-colors"
                title="Read aloud"
              >
                <Volume2 className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

        </div>
      </div>
    </div>
  );
};
