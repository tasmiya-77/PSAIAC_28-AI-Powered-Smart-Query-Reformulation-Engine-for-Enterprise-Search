"use client";

import React from "react";
import { Sparkles, FileText, AlertCircle, CheckCircle2 } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { AiAnswerResponse } from "@/types/search";

interface AiAnswerCardProps {
  aiAnswer: AiAnswerResponse;
  onSelectCitation?: (docId: string) => void;
}

export const AiAnswerCard: React.FC<AiAnswerCardProps> = ({
  aiAnswer,
  onSelectCitation,
}) => {
  const isNoAnswer = !aiAnswer.has_answer || aiAnswer.answer.includes("No relevant information found");

  return (
    <Card
      variant="glass"
      className={`border transition-all ${
        isNoAnswer
          ? "border-amber-500/30 bg-amber-950/10"
          : "border-blue-500/30 bg-blue-950/10 shadow-xl shadow-blue-500/5"
      }`}
    >
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white shadow">
            <Sparkles className="h-4 w-4" />
          </div>
          <div>
            <CardTitle className="text-base font-bold flex items-center gap-2 text-slate-900 dark:text-white">
              AI Grounded Answer
            </CardTitle>
            <span className="text-[11px] text-slate-400">
              Synthesized strictly from Top 5 retrieved enterprise document passages
            </span>
          </div>
        </div>

        <Badge variant={isNoAnswer ? "warning" : "success"} className="text-[11px]">
          {isNoAnswer ? "Insufficient Context" : `${Math.round(aiAnswer.confidence_score * 100)}% Confidence`}
        </Badge>
      </CardHeader>

      <CardContent className="pt-2 space-y-4">
        {isNoAnswer ? (
          <div className="flex items-start gap-3 p-3.5 rounded-xl border border-amber-500/20 bg-amber-500/5 text-amber-300 text-xs">
            <AlertCircle className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold">No relevant information found.</span>
              <p className="text-[11px] text-slate-400 mt-0.5">
                The ingested document store does not contain matching passages for this query. Try uploading additional docs or reformulating your query.
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-sm leading-relaxed text-slate-800 dark:text-slate-200 font-normal">
              {aiAnswer.answer}
            </p>

            {aiAnswer.citations && aiAnswer.citations.length > 0 && (
              <div className="pt-2 border-t border-slate-200 dark:border-slate-800/80">
                <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2">
                  Sources Cited:
                </div>
                <div className="flex flex-wrap gap-2">
                  {aiAnswer.citations.map((cit, idx) => (
                    <button
                      key={idx}
                      onClick={() => onSelectCitation && onSelectCitation(cit.document_id)}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border border-slate-300 dark:border-slate-800 bg-slate-200/60 dark:bg-slate-900/60 text-xs text-blue-600 dark:text-blue-400 hover:border-blue-500 transition-colors"
                    >
                      <span className="font-bold font-mono">{cit.citation_id}</span>
                      <FileText className="h-3 w-3 text-slate-400" />
                      <span className="truncate max-w-[140px]">{cit.filename}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
