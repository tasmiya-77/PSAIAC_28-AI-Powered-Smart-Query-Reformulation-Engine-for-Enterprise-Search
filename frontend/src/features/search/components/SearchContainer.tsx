"use client";

import React, { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { SearchHeader } from "./SearchHeader";
import { SearchInputBar } from "./SearchInputBar";
import { SearchFiltersBar } from "./SearchFiltersBar";
import { QueryResultCard } from "./QueryResultCard";
import { AiAnswerCard } from "./AiAnswerCard";
import { SearchResultItem } from "./SearchResultItem";
import { DocumentViewerModal } from "./DocumentViewerModal";
import { SearchSkeleton } from "./SearchSkeleton";
import { SearchFilterOptions, SearchResponse, SearchResultItem as SearchResultItemType } from "@/types/search";
import { apiClient } from "@/lib/api-client";
import { Inbox, AlertCircle, ChevronLeft, ChevronRight } from "lucide-react";

const defaultFilters: SearchFilterOptions = {
  department: "all",
  file_type: "all",
  upload_date_range: "all",
  min_relevance: 0.0,
  sort_by: "relevance",
};

export const SearchContainer: React.FC = () => {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q") || "";

  const [query, setQuery] = useState(initialQuery);
  const [mode, setMode] = useState("hybrid");
  const [filters, setFilters] = useState<SearchFilterOptions>(defaultFilters);
  const [page, setPage] = useState(1);

  const [isLoading, setIsLoading] = useState(false);
  const [searchData, setSearchData] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedDoc, setSelectedDoc] = useState<SearchResultItemType | null>(null);

  const handleExecuteSearch = async (pageNum: number = 1) => {
    if (!query.trim()) return;
    setIsLoading(true);
    setError(null);

    try {
      const res = await apiClient.executeSearch({
        query,
        mode,
        filters,
        page: pageNum,
        page_size: 5,
      });
      setSearchData(res);
      setPage(pageNum);
    } catch (err: any) {
      setError(err.message || "Failed to execute enterprise search");
      setSearchData(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (initialQuery) {
      handleExecuteSearch(1);
    }
  }, []);

  return (
    <div className="space-y-6 pb-8">
      <SearchHeader />

      <SearchInputBar
        query={query}
        setQuery={setQuery}
        mode={mode}
        setMode={setMode}
        onSearch={() => handleExecuteSearch(1)}
        isLoading={isLoading}
      />

      <SearchFiltersBar
        filters={filters}
        setFilters={setFilters}
        onApplyFilters={() => handleExecuteSearch(1)}
        onResetFilters={() => {
          setFilters(defaultFilters);
          handleExecuteSearch(1);
        }}
      />

      {error && (
        <div className="flex items-center gap-2 p-4 rounded-xl border border-rose-500/30 bg-rose-500/10 text-rose-400 text-xs">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {isLoading && <SearchSkeleton />}

      {!isLoading && searchData && (
        <div className="space-y-6">
          {searchData.query_reformulation && (
            <QueryResultCard reformulation={searchData.query_reformulation} />
          )}

          {searchData.ai_answer && (
            <AiAnswerCard aiAnswer={searchData.ai_answer} />
          )}

          {searchData.results && searchData.results.length > 0 ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between text-xs text-slate-400 px-1">
                <span>Showing {searchData.results.length} of {searchData.total_results} matching document chunks</span>
                {searchData.from_cache && <span className="font-mono text-emerald-400">Cache Hit ({searchData.processing_time_ms}ms)</span>}
              </div>

              <div className="space-y-3">
                {searchData.results.map((res) => (
                  <SearchResultItem
                    key={res.chunk_id}
                    result={res}
                    onViewDocument={setSelectedDoc}
                  />
                ))}
              </div>

              {/* Pagination */}
              {searchData.total_pages > 1 && (
                <div className="flex items-center justify-between pt-4 border-t border-slate-200 dark:border-slate-800 text-xs">
                  <span className="text-slate-500">Page {searchData.page} of {searchData.total_pages}</span>
                  <div className="flex items-center space-x-2">
                    <button
                      disabled={page <= 1}
                      onClick={() => handleExecuteSearch(page - 1)}
                      className="p-1.5 rounded-lg border border-slate-300 dark:border-slate-800 text-slate-400 disabled:opacity-40"
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </button>
                    <button
                      disabled={page >= searchData.total_pages}
                      onClick={() => handleExecuteSearch(page + 1)}
                      className="p-1.5 rounded-lg border border-slate-300 dark:border-slate-800 text-slate-400 disabled:opacity-40"
                    >
                      <ChevronRight className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center border border-dashed border-slate-300 dark:border-slate-800 rounded-xl bg-slate-100/40 dark:bg-slate-950/20">
              <Inbox className="h-10 w-10 text-slate-400 mb-2" />
              <div className="text-sm font-semibold text-slate-700 dark:text-slate-300">No matching search results</div>
              <p className="text-xs text-slate-500 max-w-sm mt-1">Try lowering the minimum relevance score or clearing file format filters.</p>
            </div>
          )}
        </div>
      )}

      <DocumentViewerModal
        document={selectedDoc}
        onClose={() => setSelectedDoc(null)}
      />
    </div>
  );
};
