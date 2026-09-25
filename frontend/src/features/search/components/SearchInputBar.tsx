"use client";

import React, { useState } from "react";
import { Search, Sparkles, X, Loader2, SlidersHorizontal, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/Button";

interface SearchInputBarProps {
  query: string;
  setQuery: (q: string) => void;
  mode: string;
  setMode: (m: string) => void;
  onSearch: () => void;
  isLoading: boolean;
}

export const SearchInputBar: React.FC<SearchInputBarProps> = ({
  query,
  setQuery,
  mode,
  setMode,
  onSearch,
  isLoading,
}) => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSearch();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="relative flex items-center rounded-2xl border border-slate-300 dark:border-slate-800 bg-white/90 dark:bg-slate-900/80 p-2 shadow-xl backdrop-blur-xl focus-within:border-blue-500/80 focus-within:ring-4 focus-within:ring-blue-500/15 transition-all">
        <div className="pl-3 text-blue-500">
          <Search className="h-5 w-5" />
        </div>

        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search enterprise documents or ask a complex query..."
          className="w-full bg-transparent px-3 py-2.5 text-sm sm:text-base text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none"
        />

        {query && (
          <button
            type="button"
            onClick={() => setQuery("")}
            className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-white transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        )}

        <Button
          type="submit"
          disabled={!query.trim() || isLoading}
          size="md"
          className="gap-2 rounded-xl shrink-0"
        >
          {isLoading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Searching...</span>
            </>
          ) : (
            <>
              <span>Search</span>
              <ArrowRight className="h-4 w-4" />
            </>
          )}
        </Button>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-2 px-1 text-xs">
        <div className="flex items-center gap-1.5 text-slate-500 font-medium">
          <SlidersHorizontal className="h-3.5 w-3.5" />
          <span>Retrieval Engine:</span>
        </div>

        <div className="flex items-center gap-1 bg-slate-200/60 dark:bg-slate-900/60 p-1 rounded-xl border border-slate-300 dark:border-slate-800">
          {[
            { id: "hybrid", label: "Hybrid RRF" },
            { id: "semantic", label: "Semantic Vector" },
            { id: "lexical", label: "BM25 Keyword" },
          ].map((m) => (
            <button
              key={m.id}
              type="button"
              onClick={() => setMode(m.id)}
              className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                mode === m.id
                  ? "bg-blue-600 text-white shadow-sm"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>
    </form>
  );
};
