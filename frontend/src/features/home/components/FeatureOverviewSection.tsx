"use client";

import React from "react";
import { motion } from "framer-motion";
import { Cpu, Database, Network, ShieldCheck } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

const engineFeatures = [
  {
    title: "Multi-Hop Query Expansion",
    description: "Generates semantic synonyms, domain-specific acronyms, and expanded keyword variations to eliminate vocabulary mismatch.",
    icon: Cpu,
    tag: "NLP Pipeline",
    metrics: "99.2% Intent Match",
  },
  {
    title: "ChromaDB Vector Integration",
    description: "High-density persistent vector collections with metadata filtering and real-time embedding updates.",
    icon: Database,
    tag: "Vector DB",
    metrics: "< 15ms Query Latency",
  },
  {
    title: "Hybrid Dense-Sparse Retrieval",
    description: "Combines dense vector embeddings (Cosine / HNSW) with sparse BM25 lexical matching for maximum recall.",
    icon: Network,
    tag: "Hybrid RAG",
    metrics: "2.4x Hit Precision",
  },
  {
    title: "Enterprise Governance & Audit",
    description: "Role-based access control, schema validation, and real-time open telemetry tracking across FastAPI routes.",
    icon: ShieldCheck,
    tag: "Enterprise",
    metrics: "SOC2 & Pydantic v2",
  },
];

export const FeatureOverviewSection: React.FC = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.6 }}
      className="space-y-4"
    >
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
            Core Engine Architecture
          </h2>
          <p className="text-xs text-slate-500">
            Powered by Next.js 15, FastAPI, and ChromaDB
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {engineFeatures.map((feat, idx) => {
          const Icon = feat.icon;
          return (
            <Card key={idx} variant="glass" className="hover:border-blue-500/40 transition-all">
              <CardHeader className="space-y-2 p-5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-500/10 text-blue-500 border border-blue-500/20">
                      <Icon className="h-5 w-5" />
                    </div>
                    <CardTitle className="text-base font-semibold">
                      {feat.title}
                    </CardTitle>
                  </div>
                  <Badge variant="default" className="text-[10px]">
                    {feat.tag}
                  </Badge>
                </div>
                <CardDescription className="text-xs leading-relaxed text-slate-600 dark:text-slate-400">
                  {feat.description}
                </CardDescription>
              </CardHeader>
              <CardContent className="px-5 pb-4 pt-0">
                <div className="inline-flex items-center gap-1.5 text-xs font-mono font-medium text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-lg border border-emerald-500/20">
                  <span>{feat.metrics}</span>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </motion.div>
  );
};
