"use client";

import React, { useState } from "react";
import { apiClient } from "@/lib/api-client";
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
  const [history, setHistory] = useState<SearchHistoryItem[]>(initialHistory);

  const handleSearchSubmit = async (submittedQuery: string, mode: string) => {
    if (!submittedQuery.trim()) return;

    setIsLoading(true);
    setError("");

    try {
      const response = await apiClient.reformulateQuery({
        query: submittedQuery.trim(),
        mode,
      });

      if (!response.success || !response.data) {
        throw new Error("Query reformulation failed.");
      }

      const result = response.data;

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

