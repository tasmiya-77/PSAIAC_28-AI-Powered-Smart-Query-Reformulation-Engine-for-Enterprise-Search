"use client";

import React from "react";
import { Filter, RotateCcw } from "lucide-react";
import { SearchFilterOptions } from "@/types/search";

interface SearchFiltersBarProps {
  filters: SearchFilterOptions;
  setFilters: React.Dispatch<React.SetStateAction<SearchFilterOptions>>;
  onApplyFilters: () => void;
  onResetFilters: () => void;
}

export const SearchFiltersBar: React.FC<SearchFiltersBarProps> = ({
  filters,
  setFilters,
  onApplyFilters,
  onResetFilters,
}) => {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl border border-slate-200 dark:border-slate-800/80 bg-slate-100/60 dark:bg-slate-900/40 text-xs">
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-1.5 text-slate-500 font-semibold uppercase tracking-wider text-[11px]">
          <Filter className="h-3.5 w-3.5 text-blue-500" />
          <span>Filters:</span>
        </div>

        {/* Department Filter */}
        <div className="flex items-center gap-1.5">
          <span className="text-slate-400">Dept:</span>
          <select
            value={filters.department}
            onChange={(e) => {
              setFilters((prev) => ({ ...prev, department: e.target.value }));
              onApplyFilters();
            }}
            className="rounded-lg border border-slate-300 dark:border-slate-800 bg-white dark:bg-slate-900 px-2 py-1 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="all">All Departments</option>
            <option value="Engineering">Engineering</option>
            <option value="Legal">Legal</option>
            <option value="HR">HR</option>
            <option value="Finance">Finance</option>
          </select>
        </div>

        {/* File Type Filter */}
        <div className="flex items-center gap-1.5">
          <span className="text-slate-400">Type:</span>
          <select
            value={filters.file_type}
            onChange={(e) => {
              setFilters((prev) => ({ ...prev, file_type: e.target.value }));
              onApplyFilters();
            }}
            className="rounded-lg border border-slate-300 dark:border-slate-800 bg-white dark:bg-slate-900 px-2 py-1 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="all">All Formats</option>
            <option value="pdf">PDF (.pdf)</option>
            <option value="docx">DOCX (.docx)</option>
            <option value="txt">TXT (.txt)</option>
            <option value="md">Markdown (.md)</option>
          </select>
        </div>

        {/* Minimum Relevance Threshold */}
        <div className="flex items-center gap-1.5">
          <span className="text-slate-400">Min Score:</span>
          <select
            value={filters.min_relevance}
            onChange={(e) => {
              setFilters((prev) => ({ ...prev, min_relevance: parseFloat(e.target.value) }));
              onApplyFilters();
            }}
            className="rounded-lg border border-slate-300 dark:border-slate-800 bg-white dark:bg-slate-900 px-2 py-1 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value={0.0}>Any Score</option>
            <option value={0.5}>&gt; 50% Match</option>
            <option value={0.7}>&gt; 70% Match</option>
            <option value={0.85}>&gt; 85% High Match</option>
          </select>
        </div>
      </div>

      <button
        onClick={onResetFilters}
        className="flex items-center gap-1 text-[11px] text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
      >
        <RotateCcw className="h-3 w-3" />
        <span>Reset</span>
      </button>
    </div>
  );
};
