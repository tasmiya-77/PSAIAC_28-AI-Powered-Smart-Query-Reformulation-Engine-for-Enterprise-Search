"use client";

import React from "react";
import { Search, Sparkles, ShieldCheck } from "lucide-react";
import { Badge } from "@/components/ui/Badge";

export const SearchHeader: React.FC = () => {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <div className="flex items-center gap-2">
          <h2 className="text-2xl font-extrabold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            <Search className="h-6 w-6 text-blue-500" />
            Enterprise Hybrid Search
          </h2>
          <Badge variant="default" className="text-[10px]">
            BM25 + Vector RRF
          </Badge>
        </div>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
          Perform high-precision RAG search across ingested documents with AI cross-encoder reranking.
        </p>
      </div>

      <div className="flex items-center gap-2 text-xs font-mono text-slate-500">
        <Sparkles className="h-4 w-4 text-indigo-400" />
        <span>Gemini 2.5 Grounded RAG</span>
        <ShieldCheck className="h-4 w-4 text-emerald-400 ml-2" />
        <span>Cached</span>
      </div>
    </div>
  );
};
