"use client";

import React, { useState } from "react";
import { apiClient } from "@/lib/api-client";
import { QueryExplainability } from "@/types/api";
import { HeroSection } from "./HeroSection";
import { SearchBarSection } from "./SearchBarSection";
import { SuggestionChipsSection } from "./SuggestionChipsSection";
import { QuickActionsSection } from "./QuickActionsSection";
import { RecentSearchesSection, SearchHistoryItem } from "./RecentSearchesSection";
import { FeatureOverviewSection } from "./FeatureOverviewSection";
import { FooterSection } from "./FooterSection";

const initialHistory: SearchHistoryItem[] = [
  {
    id: "hist-1",
    originalQuery: "Optimize PostgreSQL vector index latency",
    expandedTerms: ["pgvector indexing", "HNSW tuning", "cosine similarity performance"],
    mode: "Hybrid",
    timestamp: "10 mins ago",
    hitCount: 142,
  },
  {
    id: "hist-2",
    originalQuery: "FastAPI async database connection pool setup",
    expandedTerms: ["asyncpg pool size", "SQLAlchemy async engine", "connection leak debug"],
    mode: "Semantic",
    timestamp: "1 hour ago",
    hitCount: 89,
  },
];

export const HomeContainer: React.FC = () => {
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<QueryExplainability | null>(null);
  const [history, setHistory] = useState<SearchHistoryItem[]>(initialHistory);

  const handleSearchSubmit = async (submittedQuery: string, mode: string) => {
    if (!submittedQuery.trim()) return;

    setIsLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await apiClient.reformulateQuery({
        query: submittedQuery.trim(),
        mode,
      });

      if (!response.success || !response.data) {
        throw new Error("Query reformulation failed.");
      }

      const result = response.data;
      setResult(result);

      const newItem: SearchHistoryItem = {
        id: `hist-${Date.now()}`,
        originalQuery: result.original_query,
        expandedTerms: [
          result.best_query,
          ...result.added_keywords,
        ].filter(Boolean),
        mode: mode.toUpperCase(),
        timestamp: "Just now",
        hitCount: 0,
        provider: result.provider_used || "Unknown",
        confidence: result.confidence_score,
      };

      setHistory((prev) => [newItem, ...prev]);
    } catch (err) {
      console.error("Query reformulation error:", err);
      setError(
        err instanceof Error
          ? err.message
          : "Unable to connect to the backend."
      );
    } finally {
      setIsLoading(false);
    }
  };
  const handleSelectQuery = (selected: string) => {
    setQuery(selected);
  };

  const handleRemoveHistoryItem = (id: string) => {
    setHistory((prev) => prev.filter((item) => item.id !== id));
  };

  const handleClearHistory = () => {
    setHistory([]);
  };

  return (
    <div className="space-y-8 pb-8">
      {/* 1. Hero Section */}
      <HeroSection />

      {/* 2. Large AI Search Bar */}
      <SearchBarSection
        query={query}
        setQuery={setQuery}
        onSearchSubmit={handleSearchSubmit}
        isLoading={isLoading}
      />

      {/* AI Reformulation Results */}
      {result && (
        <section className="space-y-5 rounded-2xl border border-blue-500/20 bg-slate-900/70 p-5 shadow-lg">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-bold text-white">AI Reformulation Results</h2>
              <p className="mt-1 text-sm text-slate-400">Your query has been analyzed and expanded.</p>
            </div>
            <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-sm font-semibold text-emerald-400">
              {Math.round(result.confidence_score * 100)}% Confidence
            </span>
          </div>

          <div className="rounded-xl border border-blue-500/30 bg-blue-500/5 p-4">
            <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-blue-400">Best Reformulated Query</p>
            <p className="text-lg font-semibold text-white">{result.best_query}</p>
          </div>

          <div>
            <h3 className="mb-3 font-semibold text-white">Candidate Queries</h3>
            <div className="space-y-3">
              {result.candidate_queries.map((candidate) => (
                <div key={candidate.rank} className="rounded-xl border border-slate-700 bg-slate-800/60 p-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex gap-3">
                      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-blue-500/15 text-sm font-bold text-blue-400">
                        {candidate.rank}
                      </span>
                      <div>
                        <p className="font-medium text-slate-100">{candidate.query}</p>
                        <p className="mt-1 text-xs text-slate-400">{candidate.strategy.replace(/_/g, " ")}</p>
                      </div>
                    </div>
                    <span className="shrink-0 text-sm font-semibold text-emerald-400">
                      {Math.round(candidate.score * 100)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-xl bg-slate-800/60 p-3">
              <p className="text-xs text-slate-400">Detected Intent</p>
              <p className="mt-1 font-medium text-white">{result.intent}</p>
            </div>
            <div className="rounded-xl bg-slate-800/60 p-3">
              <p className="text-xs text-slate-400">AI Provider</p>
              <p className="mt-1 font-medium text-white">{result.provider_used || "Unknown"}</p>
            </div>
          </div>

          {result.added_keywords.length > 0 && (
            <div>
              <p className="mb-2 text-sm font-semibold text-slate-300">Added Keywords</p>
              <div className="flex flex-wrap gap-2">
                {result.added_keywords.map((keyword, index) => (
                  <span key={`${keyword}-${index}`} className="rounded-full border border-blue-500/20 bg-blue-500/10 px-3 py-1 text-xs text-blue-300">
                    {keyword}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="rounded-xl bg-slate-800/60 p-3">
            <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-slate-400">AI Explanation</p>
            <p className="text-sm leading-relaxed text-slate-300">{result.explanation}</p>
          </div>
        </section>
      )}

      {/* 3. "Try these queries" Suggestion Chips */}
      {error && (
        <div role="alert" className="rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-500">{error}</div>
      )}
      <SuggestionChipsSection onSelectQuery={handleSelectQuery} />

      {/* 4. Quick Actions Cards */}
      <QuickActionsSection />

      {/* 5. Recent Searches Card */}
      <RecentSearchesSection
        history={history}
        onRemoveItem={handleRemoveHistoryItem}
        onClearAll={handleClearHistory}
        onSelectQuery={handleSelectQuery}
      />

      {/* 6. Feature Overview Cards */}
      <FeatureOverviewSection />

      {/* 7. Enterprise Footer */}
      <FooterSection />
    </div>
  );
};


