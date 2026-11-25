"use client";

import React, { useState } from "react";
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
  const [history, setHistory] = useState<SearchHistoryItem[]>(initialHistory);

  const handleSearchSubmit = (submittedQuery: string, mode: string) => {
    setIsLoading(true);
    setTimeout(() => {
      const newItem: SearchHistoryItem = {
        id: `hist-${Date.now()}`,
        originalQuery: submittedQuery,
        expandedTerms: [
          `${submittedQuery} semantics`,
          `synonym expansion`,
          `vector embedding match`,
        ],
        mode: mode.toUpperCase(),
        timestamp: "Just now",
        hitCount: Math.floor(Math.random() * 100) + 20,
      };

      setHistory((prev) => [newItem, ...prev]);
      setIsLoading(false);
    }, 600);
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
