"use client";

import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Search, UploadCloud, BarChart3, Bot, ArrowRight } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";

const quickActions = [
  {
    title: "Search Documents",
    description: "Perform hybrid vector & BM25 retrieval over ingested docs.",
    icon: Search,
    href: "/search",
    color: "from-blue-600 to-cyan-600",
    badge: "Vector Search",
  },
  {
    title: "Upload Documents",
    description: "Ingest PDFs, markdown, and text files into ChromaDB.",
    icon: UploadCloud,
    href: "/upload",
    color: "from-indigo-600 to-purple-600",
    badge: "Ingestion",
  },
  {
    title: "Analytics Telemetry",
    description: "Monitor query latency, hit precision, and expansion logs.",
    icon: BarChart3,
    href: "/analytics",
    color: "from-emerald-600 to-teal-600",
    badge: "Metrics",
  },
  {
    title: "AI Reformulation Assistant",
    description: "Interactive agentic assistant for query optimization.",
    icon: Bot,
    href: "/search?assistant=true",
    color: "from-amber-600 to-orange-600",
    badge: "Agentic AI",
  },
];

export const QuickActionsSection: React.FC = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.4 }}
      className="space-y-4"
    >
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
          Quick Actions
        </h2>
        <span className="text-xs text-slate-500">Core Engine Workflows</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {quickActions.map((action, idx) => {
          const Icon = action.icon;
          return (
            <Link key={idx} href={action.href}>
              <Card
                variant="glass"
                className="group relative h-full hover:border-blue-500/50 hover:shadow-2xl transition-all duration-300"
              >
                <CardHeader className="space-y-3 p-5">
                  <div className="flex items-center justify-between">
                    <div
                      className={`flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr ${action.color} text-white shadow-lg`}
                    >
                      <Icon className="h-5 w-5" />
                    </div>
                    <ArrowRight className="h-4 w-4 text-slate-400 group-hover:text-blue-500 group-hover:translate-x-1 transition-all" />
                  </div>
                  <div>
                    <CardTitle className="text-base font-semibold group-hover:text-blue-400 transition-colors">
                      {action.title}
                    </CardTitle>
                    <CardDescription className="text-xs text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">
                      {action.description}
                    </CardDescription>
                  </div>
                </CardHeader>
              </Card>
            </Link>
          );
        })}
      </div>
    </motion.div>
  );
};
