import React from 'react';
import { FileText, FileCode, FileSpreadsheet, FileImage, File, Trash2, Eye } from 'lucide-react';
import type { UploadedFile, FileType } from '../types/chat';

interface FileBadgeProps {
  file: UploadedFile;
  onRemove?: (id: string) => void;
  onView?: (file: UploadedFile) => void;
  compact?: boolean;
  showDetails?: boolean;
}

export const getFileIcon = (type: FileType, className: string = "w-4 h-4") => {
  switch (type) {
    case 'pdf':
      return <FileText className={`${className} text-rose-400`} />;
    case 'docx':
      return <FileText className={`${className} text-blue-400`} />;
    case 'code':
      return <FileCode className={`${className} text-emerald-400`} />;
    case 'csv':
      return <FileSpreadsheet className={`${className} text-amber-400`} />;
    case 'image':
      return <FileImage className={`${className} text-purple-400`} />;
    default:
      return <File className={`${className} text-slate-400`} />;
  }
};

export const getFileColorClass = (type: FileType) => {
  switch (type) {
    case 'pdf':
      return 'bg-rose-500/10 border-rose-500/20 text-rose-300';
    case 'docx':
      return 'bg-blue-500/10 border-blue-500/20 text-blue-300';
    case 'code':
      return 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300';
    case 'csv':
      return 'bg-amber-500/10 border-amber-500/20 text-amber-300';
    case 'image':
      return 'bg-purple-500/10 border-purple-500/20 text-purple-300';
    default:
      return 'bg-slate-500/10 border-slate-500/20 text-slate-300';
  }
};

export const FileBadge: React.FC<FileBadgeProps> = ({
  file,
  onRemove,
  onView,
  compact = false,
  showDetails = false
}) => {
  if (compact) {
    return (
      <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-medium ${getFileColorClass(file.type)} transition-all hover:brightness-110`}>
        {getFileIcon(file.type, "w-3.5 h-3.5")}
        <span className="max-w-[140px] truncate">{file.name}</span>
        {file.pages && (
          <span className="opacity-60 text-[10px]">({file.pages}p)</span>
        )}
        {onRemove && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onRemove(file.id);
            }}
            className="ml-1 text-slate-400 hover:text-rose-400 transition-colors p-0.5 rounded"
            title="Remove attachment"
          >
            &times;
          </button>
        )}
      </div>
    );
  }

  return (
    <div className={`group flex items-center justify-between p-3 rounded-xl border ${getFileColorClass(file.type)} backdrop-blur-md transition-all duration-200 hover:border-indigo-500/40 hover:shadow-lg hover:shadow-indigo-500/5`}>
      <div className="flex items-center gap-3 min-w-0">
        <div className="p-2.5 rounded-lg bg-slate-900/60 border border-white/5 flex-shrink-0">
          {getFileIcon(file.type, "w-5 h-5")}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h4 className="text-sm font-semibold text-slate-100 truncate" title={file.name}>
              {file.name}
            </h4>
            <span className="px-1.5 py-0.5 text-[10px] uppercase font-bold tracking-wider rounded bg-slate-800 text-slate-400 border border-slate-700">
              {file.type}
            </span>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
            <span>{file.size}</span>
            {file.pages && <span>• {file.pages} pages</span>}
            {file.tokensCount && <span>• ~{(file.tokensCount / 1000).toFixed(1)}k tokens</span>}
            {file.status === 'indexing' && (
              <span className="text-amber-400 flex items-center gap-1 animate-pulse">
                • Indexing...
              </span>
            )}
          </div>
          {showDetails && file.summary && (
            <p className="text-xs text-slate-400 mt-2 line-clamp-2 bg-slate-950/40 p-2 rounded-lg border border-white/5">
              {file.summary}
            </p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-1 ml-3 flex-shrink-0 opacity-90 group-hover:opacity-100">
        {onView && (
          <button
            onClick={() => onView(file)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors flex items-center gap-1 text-xs"
            title="Inspect document side-by-side"
          >
            <Eye className="w-4 h-4" />
            <span className="hidden sm:inline">Inspect</span>
          </button>
        )}
        {onRemove && (
          <button
            onClick={() => onRemove(file.id)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
            title="Delete file"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};
