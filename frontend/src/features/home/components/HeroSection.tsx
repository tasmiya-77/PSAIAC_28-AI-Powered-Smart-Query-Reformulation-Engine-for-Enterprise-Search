"use client";

import React from "react";
import { motion } from "framer-motion";
import { Sparkles, Shield, Cpu } from "lucide-react";
import { Badge } from "@/components/ui/Badge";

export const HeroSection: React.FC = () => {
  return (
    <div className="space-y-4 text-center sm:text-left">
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex flex-wrap items-center justify-center sm:justify-start gap-2"
      >
        <Badge variant="default" className="gap-1.5 py-1 px-3">
          <Sparkles className="h-3.5 w-3.5 text-blue-400 animate-pulse" />
          Next-Gen AI RAG Expansion
        </Badge>
        <span className="inline-flex items-center gap-1 text-xs text-slate-500 font-mono">
          <Shield className="h-3.5 w-3.5 text-emerald-400" />
          ChromaDB Vector Store Connected
        </span>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="space-y-2"
      >
        <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight bg-gradient-to-r from-slate-900 via-blue-600 to-indigo-600 dark:from-white dark:via-blue-300 dark:to-indigo-300 bg-clip-text text-transparent">
          AI-Powered Smart Query Reformulation Engine
        </h1>
        <p className="text-base sm:text-lg text-slate-600 dark:text-slate-400 max-w-3xl leading-relaxed">
          Transform vague user queries into high-precision, multi-dimensional semantic search vectors.
          Enhance information retrieval hit rates across enterprise document stores.
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.2 }}
        className="flex flex-wrap items-center gap-4 text-xs font-mono text-slate-500 pt-1"
      >
        <div className="flex items-center gap-1.5">
          <Cpu className="h-4 w-4 text-blue-500" />
          <span>FastAPI Async Gateway</span>
        </div>
        <span>•</span>
        <span>Hybrid Dense-Sparse RAG</span>
        <span>•</span>
        <span>Real-time Telemetry</span>
      </motion.div>
    </div>
  );
};
