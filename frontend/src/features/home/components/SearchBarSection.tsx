"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { Search, Sparkles, X, Loader2, SlidersHorizontal, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/Button";

interface SearchBarSectionProps {
  query: string;
  setQuery: (q: string) => void;
  onSearchSubmit: (query: string, mode: string) => void;
  isLoading: boolean;
}

export const SearchBarSection: React.FC<SearchBarSectionProps> = ({
  query,
  setQuery,
  onSearchSubmit,
  isLoading,
}) => {
  const [searchMode, setSearchMode] = useState<string>("hybrid");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearchSubmit(query, searchMode);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      className="w-full"
    >
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="relative flex items-center rounded-2xl border border-slate-300 dark:border-slate-800 bg-white/90 dark:bg-slate-900/80 p-2 shadow-2xl backdrop-blur-xl focus-within:border-blue-500/80 focus-within:ring-4 focus-within:ring-blue-500/15 transition-all">
          <div className="pl-3 text-blue-500">
            <Sparkles className="h-6 w-6 animate-pulse" />
          </div>

          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter a raw query to reformulate (e.g. 'how to fix database latency in production')..."
            className="w-full bg-transparent px-4 py-3 text-base sm:text-lg text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none"
          />

          {query && (
            <button
              type="button"
              onClick={() => setQuery("")}
              className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-white transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          )}

          <Button
            type="submit"
            disabled={!query.trim() || isLoading}
            size="lg"
            className="gap-2 rounded-xl shrink-0"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                <span>Reformulating...</span>
              </>
            ) : (
              <>
                <span>Reformulate Query</span>
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </Button>
        </div>

        {/* Search Mode Toggles */}
        <div className="flex flex-wrap items-center justify-between gap-3 px-2 text-xs">
          <div className="flex items-center gap-1.5 text-slate-500 font-medium">
            <SlidersHorizontal className="h-3.5 w-3.5" />
            <span>Expansion Mode:</span>
          </div>

          <div className="flex items-center gap-1.5 bg-slate-200/60 dark:bg-slate-900/60 p-1 rounded-xl border border-slate-300 dark:border-slate-800">
            {[
              { id: "hybrid", label: "Hybrid (Dense + Sparse)" },
              { id: "semantic", label: "Semantic Expansion" },
              { id: "vector", label: "Vector Search" },
              { id: "lexical", label: "Lexical BM25" },
            ].map((mode) => (
              <button
                key={mode.id}
                type="button"
                onClick={() => setSearchMode(mode.id)}
                className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                  searchMode === mode.id
                    ? "bg-blue-600 text-white shadow-sm"
                    : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
                }`}
              >
                {mode.label}
              </button>
            ))}
          </div>
        </div>
      </form>
    </motion.div>
  );
};
