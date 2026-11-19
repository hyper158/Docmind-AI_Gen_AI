import React, { useState, useRef } from 'react';
import { 
  X, UploadCloud, FileText, CheckCircle2, 
  FileCode, FileSpreadsheet, ShieldCheck, Sparkles, Loader2, AlertCircle
} from 'lucide-react';
import type { UploadedFile } from '../types/chat';
import { api } from '../services/api';

interface FileUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadComplete: (files: UploadedFile[]) => void;
}

export const FileUploadModal: React.FC<FileUploadModalProps> = ({
  isOpen,
  onClose,
  onUploadComplete
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [uploadingFiles, setUploadingFiles] = useState<{
    file: File;
    progress: number;
    status: 'uploading' | 'indexing' | 'done' | 'error';
    errorText?: string;
  }[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const processFiles = async (files: File[]) => {
    setErrorMessage(null);
    const fileEntries = files.map(f => ({
      file: f,
      progress: 25,
      status: 'uploading' as const
    }));

    setUploadingFiles(fileEntries);

    const uploadedDocs: UploadedFile[] = [];

    for (const file of files) {
      try {
        // Transition to indexing state
        setUploadingFiles(prev =>
          prev.map(item => item.file === file ? { ...item, progress: 65, status: 'indexing' } : item)
        );

        // Actual backend upload & vector indexing call
        const uploadedFile = await api.uploadDocument(file);

        setUploadingFiles(prev =>
          prev.map(item => item.file === file ? { ...item, progress: 100, status: 'done' } : item)
        );
        uploadedDocs.push(uploadedFile);
      } catch (err: any) {
        const msg = err.message || 'Failed to upload document.';
        setErrorMessage(msg);
        setUploadingFiles(prev =>
          prev.map(item => item.file === file ? { ...item, status: 'error', errorText: msg } : item)
        );
      }
    }

    if (uploadedDocs.length > 0) {
      setTimeout(() => {
        onUploadComplete(uploadedDocs);
        setUploadingFiles([]);
        onClose();
      }, 700);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFiles(Array.from(e.target.files));
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-xl bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl p-6 sm:p-8 space-y-6">
        
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="space-y-2 text-center sm:text-left">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" /> PyPDF2 Extraction & FAISS Vector Indexing
          </div>
          <h2 className="text-xl font-bold text-white tracking-tight">
            Upload Syllabus or Study PDF
          </h2>
          <p className="text-xs text-slate-400">
            Upload your course syllabus or notes in PDF format. DocMind will extract text page-by-page and create local vector embeddings for accurate Q&A citations.
          </p>
        </div>

        {/* Error Alert if any */}
        {errorMessage && (
          <div className="flex items-start gap-2.5 p-3 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
            <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">{errorMessage}</div>
          </div>
        )}

        {/* Dropzone Area */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`relative border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-200 flex flex-col items-center justify-center gap-4 ${
            isDragging 
              ? 'border-indigo-500 bg-indigo-500/10 scale-[1.01]' 
              : 'border-slate-700 hover:border-indigo-500/50 bg-slate-950/50 hover:bg-slate-950/80'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            accept=".pdf"
            onChange={handleFileSelect}
          />

          <div className="w-16 h-16 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 shadow-inner group-hover:scale-110 transition-transform">
            <UploadCloud className="w-8 h-8 animate-bounce" />
          </div>

          <div className="space-y-1">
            <p className="text-sm font-semibold text-slate-200">
              Drag & drop your PDF file here, or <span className="text-indigo-400 underline decoration-indigo-400/50">browse files</span>
            </p>
            <p className="text-xs text-slate-500">
              PDF Documents only (Up to 50 MB per file)
            </p>
          </div>
        </div>

        {/* Uploading Files Progress Display */}
        {uploadingFiles.length > 0 && (
          <div className="space-y-3 pt-2">
            <div className="text-xs font-semibold text-slate-300">
              Processing & Vector Indexing...
            </div>
            {uploadingFiles.map((item, idx) => (
              <div key={idx} className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2 font-medium text-slate-200">
                    {item.status === 'done' && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                    {item.status === 'error' && <AlertCircle className="w-4 h-4 text-rose-400" />}
                    {(item.status === 'uploading' || item.status === 'indexing') && (
                      <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />
                    )}
                    <span className="truncate max-w-[220px]">{item.file.name}</span>
                  </div>
                  <span className="text-[11px] text-slate-400">
                    {item.status === 'uploading' && 'Uploading PDF...'}
                    {item.status === 'indexing' && 'Extracting PyPDF2 & Indexing FAISS...'}
                    {item.status === 'done' && 'Ready for Q&A!'}
                    {item.status === 'error' && (item.errorText || 'Error processing file')}
                  </span>
                </div>
                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                  <div 
                    className={`h-full transition-all duration-300 ${
                      item.status === 'error'
                        ? 'bg-rose-500'
                        : 'bg-gradient-to-r from-indigo-500 via-purple-500 to-cyan-400'
                    }`}
                    style={{ width: `${item.progress}%` }} 
                  />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Supported Formats Pill Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-slate-800/80">
          <div className="flex items-center gap-2 p-2 rounded-xl bg-slate-950/50 border border-slate-800 text-[11px] text-slate-400">
            <FileText className="w-3.5 h-3.5 text-rose-400" /> Syllabus PDF
          </div>
          <div className="flex items-center gap-2 p-2 rounded-xl bg-slate-950/50 border border-slate-800 text-[11px] text-slate-400">
            <FileText className="w-3.5 h-3.5 text-blue-400" /> Lecture Notes
          </div>
          <div className="flex items-center gap-2 p-2 rounded-xl bg-slate-950/50 border border-slate-800 text-[11px] text-slate-400">
            <FileCode className="w-3.5 h-3.5 text-emerald-400" /> Lab Manuals
          </div>
          <div className="flex items-center gap-2 p-2 rounded-xl bg-slate-950/50 border border-slate-800 text-[11px] text-slate-400">
            <FileSpreadsheet className="w-3.5 h-3.5 text-amber-400" /> Exam Guides
          </div>
        </div>

        {/* Privacy Note */}
        <div className="flex items-center justify-center gap-2 text-[11px] text-slate-500 pt-1">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> Local Vector Embeddings • Private & Secure
        </div>

      </div>
    </div>
  );
};
