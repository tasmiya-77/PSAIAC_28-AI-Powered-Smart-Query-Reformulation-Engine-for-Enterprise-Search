"use client";

import React from "react";
import { Sparkles, ArrowRight, Zap, Target } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { QueryExplainability } from "@/types/api";

interface QueryResultCardProps {
  reformulation: QueryExplainability;
}

export const QueryResultCard: React.FC<QueryResultCardProps> = ({
  reformulation,
}) => {
  return (
    <Card variant="glass" className="border-indigo-500/20 bg-indigo-950/10">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div className="flex items-center gap-2">
          <Zap className="h-4 w-4 text-indigo-400" />
          <CardTitle className="text-sm font-bold text-slate-800 dark:text-slate-200">
            Query Expansion & Reformulation Analysis
          </CardTitle>
        </div>
        <div className="flex items-center gap-2">
          {reformulation.provider_used && (
            <Badge variant="outline" className="text-[10px] text-cyan-400 border-cyan-500/30 bg-cyan-950/20">
              Provider: {reformulation.provider_used}
            </Badge>
          )}
          <Badge variant="default" className="text-[10px]">
            Intent: {reformulation.intent}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-2.5 text-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-2.5 rounded-lg bg-slate-900/60 border border-slate-800">
          <div className="space-y-0.5">
            <span className="text-[10px] uppercase font-bold text-slate-500">Original Query:</span>
            <div className="text-slate-400 font-mono">{reformulation.original_query}</div>
          </div>
          <ArrowRight className="h-4 w-4 text-slate-500 shrink-0 hidden sm:block" />
          <div className="space-y-0.5 sm:text-right">
            <span className="text-[10px] uppercase font-bold text-blue-400">Best Reformulated Query:</span>
            <div className="text-blue-300 font-mono font-semibold">{reformulation.best_query}</div>
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-400 pt-1">
          <div className="flex items-center gap-1">
            <Target className="h-3.5 w-3.5 text-emerald-400" />
            <span>Entities:</span>
            <span className="text-slate-200 font-semibold">
              {reformulation.entities.length > 0 ? reformulation.entities.join(", ") : "General Domain"}
            </span>
          </div>

          <div className="flex items-center gap-1">
            <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
            <span>Explanation:</span>
            <span className="text-slate-300 truncate max-w-sm">{reformulation.explanation}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
