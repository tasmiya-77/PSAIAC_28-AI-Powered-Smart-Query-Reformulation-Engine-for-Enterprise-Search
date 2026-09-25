"use client";

import React, { useState } from "react";
import { FileText, ArrowUpRight, CheckCircle2, Building, Calendar, HardDrive, HelpCircle, ChevronDown, ChevronUp, Sparkles, ThumbsUp, ThumbsDown, MessageSquare, Send, Check } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { SearchResultItem as SearchResultItemType } from "@/types/search";
import { apiClient } from "@/lib/api-client";

interface SearchResultItemProps {
  result: SearchResultItemType;
  onViewDocument: (result: SearchResultItemType) => void;
}

export const SearchResultItem: React.FC<SearchResultItemProps> = ({
  result,
  onViewDocument,
}) => {
  const [showExplanation, setShowExplanation] = useState(false);
  const [feedbackRating, setFeedbackRating] = useState<"helpful" | "not_helpful" | null>(null);
  const [feedbackComment, setFeedbackComment] = useState("");
  const [showCommentBox, setShowCommentBox] = useState(false);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const getBadgeVariant = (confidence: string) => {
    if (confidence === "High") return "success";
    if (confidence === "Medium") return "warning";
    return "outline";
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const handleRatingClick = async (rating: "helpful" | "not_helpful") => {
    setFeedbackRating(rating);
    setShowCommentBox(true);
  };

  const submitFeedback = async () => {
    if (!feedbackRating || isSubmitting) return;
    setIsSubmitting(true);
    try {
      await apiClient.submitFeedback({
        query: result.title || result.filename,
        document_id: result.document_id,
        chunk_id: result.chunk_id,
        filename: result.filename,
        rating: feedbackRating,
        feedback_text: feedbackComment.trim() || undefined,
      });
      setFeedbackSubmitted(true);
      setShowCommentBox(false);
    } catch {
      setFeedbackSubmitted(true);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card
      variant="glass"
      className="group hover:border-blue-500/40 hover:shadow-xl transition-all duration-200"
    >
      <CardHeader className="flex flex-row items-start justify-between pb-2 p-5">
        <div className="space-y-1 flex-1 pr-4">
          <div className="flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-md bg-blue-500/10 text-blue-600 dark:text-blue-400 font-mono text-xs font-bold border border-blue-500/20">
              #{result.rank ?? 1}
            </span>
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-500/10 text-blue-500 border border-blue-500/20">
              <FileText className="h-4 w-4" />
            </div>
            <CardTitle
              onClick={() => onViewDocument(result)}
              className="text-base font-bold text-slate-900 dark:text-slate-100 hover:text-blue-500 cursor-pointer flex items-center gap-1.5 transition-colors"
            >
              {result.title || result.filename}
              <ArrowUpRight className="h-4 w-4 text-slate-400 group-hover:text-blue-500 transition-colors" />
            </CardTitle>
          </div>

          <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 pt-1">
            <span className="flex items-center gap-1">
              <Building className="h-3.5 w-3.5 text-slate-400" />
              {result.department}
            </span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <HardDrive className="h-3.5 w-3.5 text-slate-400" />
              {formatFileSize(result.file_size_bytes)}
            </span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <Calendar className="h-3.5 w-3.5 text-slate-400" />
              {result.upload_date.slice(0, 10)}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <Badge variant={getBadgeVariant(result.confidence)} className="text-xs font-mono font-semibold">
            {result.relevance_percentage}% ({result.confidence})
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="px-5 pb-4 pt-1 space-y-3">
        {/* Highlighted text snippet */}
        <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-normal bg-slate-100/50 dark:bg-slate-900/40 p-3 rounded-xl border border-slate-200 dark:border-slate-800">
          "{result.passage || result.highlighted_snippet || result.content.slice(0, 220)}..."
        </p>

        {/* Matched Keywords & Controls */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-slate-200/50 dark:border-slate-800/60 text-xs">
          {result.matched_keywords && result.matched_keywords.length > 0 ? (
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
              <span className="text-slate-400 font-medium">Matched:</span>
              <div className="flex flex-wrap gap-1">
                {result.matched_keywords.map((kw, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-0.5 rounded-md bg-blue-500/10 text-blue-600 dark:text-blue-400 text-[11px] font-mono"
                  >
                    {kw}
                  </span>
                ))}
              </div>
            </div>
          ) : (
            <div />
          )}

          <div className="flex items-center gap-2 ml-auto">
            {/* Feedback Controls */}
            {feedbackSubmitted ? (
              <span className="flex items-center gap-1 text-[11px] text-emerald-400 font-medium bg-emerald-500/10 px-2 py-0.5 rounded-md border border-emerald-500/20">
                <Check className="h-3 w-3" /> Feedback Received
              </span>
            ) : (
              <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-900/60 p-1 rounded-lg border border-slate-200 dark:border-slate-800">
                <button
                  onClick={() => handleRatingClick("helpful")}
                  title="Helpful result"
                  className={`p-1 rounded transition-colors ${
                    feedbackRating === "helpful"
                      ? "bg-emerald-500/20 text-emerald-400"
                      : "text-slate-400 hover:text-emerald-400"
                  }`}
                >
                  <ThumbsUp className="h-3.5 w-3.5" />
                </button>
                <button
                  onClick={() => handleRatingClick("not_helpful")}
                  title="Not helpful result"
                  className={`p-1 rounded transition-colors ${
                    feedbackRating === "not_helpful"
                      ? "bg-rose-500/20 text-rose-400"
                      : "text-slate-400 hover:text-rose-400"
                  }`}
                >
                  <ThumbsDown className="h-3.5 w-3.5" />
                </button>
              </div>
            )}

            <button
              onClick={() => setShowExplanation(!showExplanation)}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-blue-500/10 hover:bg-blue-500/20 text-blue-600 dark:text-blue-400 font-medium text-xs transition-colors"
            >
              <HelpCircle className="h-3.5 w-3.5" />
              <span>Why this result?</span>
              {showExplanation ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
            </button>
          </div>
        </div>

        {/* Optional Comment Form overlay */}
        {showCommentBox && !feedbackSubmitted && (
          <div className="p-3 rounded-xl bg-slate-900/90 border border-blue-500/30 text-xs space-y-2 animate-in fade-in duration-200">
            <div className="flex items-center justify-between text-slate-300 font-medium">
              <span className="flex items-center gap-1">
                <MessageSquare className="h-3.5 w-3.5 text-blue-400" />
                Add optional feedback for this result ({feedbackRating === "helpful" ? "👍 Helpful" : "👎 Not Helpful"})
              </span>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={feedbackComment}
                onChange={(e) => setFeedbackComment(e.target.value)}
                placeholder="Why was this result helpful or unhelpful?"
                className="flex-1 bg-slate-950 text-slate-200 text-xs px-3 py-1.5 rounded-lg border border-slate-800 focus:outline-none focus:border-blue-500"
              />
              <button
                onClick={submitFeedback}
                disabled={isSubmitting}
                className="flex items-center gap-1 bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs px-3 py-1.5 rounded-lg transition-colors shrink-0 disabled:opacity-50"
              >
                <Send className="h-3 w-3" />
                {isSubmitting ? "Submitting..." : "Submit"}
              </button>
            </div>
          </div>
        )}

        {/* Expandable "Why this result?" Panel */}
        {showExplanation && (
          <div className="p-4 rounded-xl bg-slate-900/90 text-slate-200 border border-blue-500/30 text-xs space-y-3 shadow-lg animate-in fade-in duration-200">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-2">
              <div className="flex items-center gap-1.5 font-semibold text-blue-400">
                <Sparkles className="h-4 w-4" />
                <span>Result Explainability Rationale</span>
              </div>
              <Badge variant="outline" className="text-[10px] bg-blue-950/40 text-blue-300 border-blue-800 font-mono">
                {result.retrieval_method || "Hybrid (BM25 + ChromaDB Vector)"}
              </Badge>
            </div>

            {/* Metric score pills */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center pt-1 font-mono">
              <div className="p-2 rounded-lg bg-slate-800/80 border border-slate-700/60">
                <span className="text-[10px] text-slate-400 block font-sans">Semantic Score</span>
                <span className="text-sm font-bold text-cyan-400">{result.semantic_score ?? 0.0}</span>
              </div>
              <div className="p-2 rounded-lg bg-slate-800/80 border border-slate-700/60">
                <span className="text-[10px] text-slate-400 block font-sans">BM25 Score</span>
                <span className="text-sm font-bold text-emerald-400">{result.keyword_score ?? 0.0}</span>
              </div>
              <div className="p-2 rounded-lg bg-slate-800/80 border border-slate-700/60">
                <span className="text-[10px] text-slate-400 block font-sans">BGE Rerank Score</span>
                <span className="text-sm font-bold text-purple-400">{result.rerank_score ?? 0.0}</span>
              </div>
              <div className="p-2 rounded-lg bg-slate-800/80 border border-slate-700/60">
                <span className="text-[10px] text-slate-400 block font-sans">Final Relevance</span>
                <span className="text-sm font-bold text-amber-400">{result.relevance_percentage}%</span>
              </div>
            </div>

            <p className="text-slate-300 leading-relaxed pt-1 whitespace-pre-line font-mono text-[11px]">
              {result.why_selected || result.explanation || `Ranked #${result.rank ?? 1} based on dual-path BM25 lexical keyword matching and ChromaDB Sentence Transformers semantic vector similarity, reranked with BGE Cross-Encoder.`}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};


