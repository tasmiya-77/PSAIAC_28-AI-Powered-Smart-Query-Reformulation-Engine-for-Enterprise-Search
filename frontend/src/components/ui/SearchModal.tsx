"use client";

import React, { useState } from "react";
import { Search, X, Sparkles, ArrowRight } from "lucide-react";
import { useLayout } from "@/context/LayoutContext";

export const SearchModal: React.FC = () => {
  const { searchModalOpen, closeSearchModal } = useLayout();
  const [query, setQuery] = useState("");

  if (!searchModalOpen) return null;

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      closeSearchModal();
      window.location.href = `/search?q=${encodeURIComponent(query)}`;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-2xl mx-4 rounded-2xl border border-slate-700/80 bg-slate-900 shadow-2xl overflow-hidden">
        <form onSubmit={handleSearch} className="flex items-center px-4 py-3 border-b border-slate-800">
          <Search className="h-5 w-5 text-blue-400 mr-3" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a query to reformulate or search enterprise docs..."
            className="w-full bg-transparent text-white placeholder-slate-400 text-base focus:outline-none"
            autoFocus
          />
          <button
            type="button"
            onClick={closeSearchModal}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
          >
            <X className="h-5 w-5" />
          </button>
        </form>

        <div className="p-4 space-y-3 max-h-[360px] overflow-y-auto">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Quick Actions
          </div>
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => {
                closeSearchModal();
                window.location.href = "/search";
              }}
              className="flex items-center justify-between p-3 rounded-xl border border-slate-800 bg-slate-950/40 text-left hover:border-blue-500/40 hover:bg-blue-950/20 transition-all text-xs font-medium text-slate-200"
            >
              <span className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-blue-400" />
                Query Reformulator
              </span>
              <ArrowRight className="h-3.5 w-3.5 text-slate-500" />
            </button>

            <button
              onClick={() => {
                closeSearchModal();
                window.location.href = "/upload";
              }}
              className="flex items-center justify-between p-3 rounded-xl border border-slate-800 bg-slate-950/40 text-left hover:border-indigo-500/40 hover:bg-indigo-950/20 transition-all text-xs font-medium text-slate-200"
            >
              <span className="flex items-center gap-2">
                <Search className="h-4 w-4 text-indigo-400" />
                Document Ingestion
              </span>
              <ArrowRight className="h-3.5 w-3.5 text-slate-500" />
            </button>
          </div>
        </div>

        <div className="px-4 py-2 bg-slate-950/80 border-t border-slate-800 flex justify-between items-center text-[11px] text-slate-400">
          <span>Press <kbd className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700">ESC</kbd> to exit</span>
          <span>AI-Powered Smart Query Reformulation Engine</span>
        </div>
      </div>
    </div>
  );
};
