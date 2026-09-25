"use client";

import React from "react";
import { Card, CardHeader, CardContent } from "@/components/ui/Card";

export const SearchSkeleton: React.FC = () => {
  return (
    <div className="space-y-6 animate-pulse">
      {/* AI Answer Skeleton */}
      <Card variant="glass" className="border-slate-800">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-xl bg-slate-800" />
            <div className="space-y-1">
              <div className="h-4 w-36 rounded bg-slate-800" />
              <div className="h-3 w-64 rounded bg-slate-800/60" />
            </div>
          </div>
          <div className="h-5 w-24 rounded-full bg-slate-800" />
        </CardHeader>
        <CardContent className="space-y-2 pt-2">
          <div className="h-3.5 w-full rounded bg-slate-800" />
          <div className="h-3.5 w-5/6 rounded bg-slate-800" />
          <div className="h-3.5 w-4/6 rounded bg-slate-800" />
        </CardContent>
      </Card>

      {/* Query Explainability Skeleton */}
      <Card variant="glass" className="border-slate-800">
        <CardHeader className="pb-2">
          <div className="h-4 w-48 rounded bg-slate-800" />
        </CardHeader>
        <CardContent>
          <div className="h-10 w-full rounded-lg bg-slate-800/60" />
        </CardContent>
      </Card>

      {/* Results List Skeleton */}
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <Card key={i} variant="glass" className="border-slate-800">
            <CardHeader className="flex flex-row items-start justify-between pb-2">
              <div className="space-y-2 flex-1">
                <div className="flex items-center gap-2">
                  <div className="h-7 w-7 rounded-lg bg-slate-800" />
                  <div className="h-4 w-48 rounded bg-slate-800" />
                </div>
                <div className="h-3 w-32 rounded bg-slate-800/60" />
              </div>
              <div className="h-6 w-20 rounded-full bg-slate-800" />
            </CardHeader>
            <CardContent>
              <div className="h-16 w-full rounded-xl bg-slate-800/40" />
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};
