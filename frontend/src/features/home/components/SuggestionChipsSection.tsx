"use client";

import React from "react";
import { motion } from "framer-motion";
import { Lightbulb, ArrowUpRight } from "lucide-react";

interface SuggestionChipsSectionProps {
  onSelectQuery: (query: string) => void;
}

const sampleSuggestions = [
  "Optimize PostgreSQL index for vector similarity",
  "RAG retrieval latency reduction techniques",
  "ChromaDB collection metadata filtering",
  "FastAPI async endpoint throughput benchmark",
  "Hybrid dense sparse query expansion algorithms",
];

export const SuggestionChipsSection: React.FC<SuggestionChipsSectionProps> = ({
  onSelectQuery,
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.3 }}
      className="space-y-2.5"
    >
      <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
        <Lightbulb className="h-3.5 w-3.5 text-amber-400" />
        <span>Try these queries</span>
      </div>

      <div className="flex flex-wrap gap-2">
        {sampleSuggestions.map((suggestion, idx) => (
          <button
            key={idx}
            onClick={() => onSelectQuery(suggestion)}
            className="group inline-flex items-center gap-1.5 rounded-xl border border-slate-300 dark:border-slate-800 bg-slate-100/60 dark:bg-slate-900/40 px-3.5 py-2 text-xs font-medium text-slate-700 dark:text-slate-300 hover:border-blue-500/50 hover:bg-blue-500/10 hover:text-blue-600 dark:hover:text-blue-400 transition-all"
          >
            <span>{suggestion}</span>
            <ArrowUpRight className="h-3 w-3 text-slate-400 group-hover:text-blue-500 transition-colors" />
          </button>
        ))}
      </div>
    </motion.div>
  );
};
