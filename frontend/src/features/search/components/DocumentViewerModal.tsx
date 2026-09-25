"use client";

import React from "react";
import { X, FileText, Building, Calendar, HardDrive, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { SearchResultItem } from "@/types/search";

interface DocumentViewerModalProps {
  document: SearchResultItem | null;
  onClose: () => void;
}

export const DocumentViewerModal: React.FC<DocumentViewerModalProps> = ({
  document,
  onClose,
}) => {
  if (!document) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-3xl rounded-2xl border border-slate-700/80 bg-slate-900 shadow-2xl overflow-hidden text-slate-100 flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-white shadow">
              <FileText className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                {document.filename}
              </h3>
              <div className="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
                <span>{document.department}</span>
                <span>•</span>
                <span>Chunk {document.chunk_index + 1} of {document.total_chunks}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="success" className="text-xs font-mono font-semibold">
              {document.relevance_percentage}% Match ({document.confidence})
            </Badge>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Document Content Viewport */}
        <div className="p-5 overflow-y-auto space-y-4 flex-1">
          <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 font-mono text-xs sm:text-sm leading-relaxed text-slate-300 whitespace-pre-wrap">
            {document.content}
          </div>

          {document.matched_keywords && document.matched_keywords.length > 0 && (
            <div className="p-3 rounded-xl border border-slate-800 bg-slate-900/60 text-xs">
              <span className="font-semibold text-slate-400 block mb-1">
                Extracted Term Matches:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {document.matched_keywords.map((kw, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 font-mono"
                  >
                    {kw}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-950/80 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <span>Document ID: {document.document_id}</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium transition-colors"
          >
            Close Viewer
          </button>
        </div>
      </div>
    </div>
  );
};
