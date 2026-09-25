import React, { Suspense } from "react";
import { SearchContainer } from "@/features/search/components/SearchContainer";
import { SearchSkeleton } from "@/features/search/components/SearchSkeleton";

export const metadata = {
  title: "Enterprise Search Workbench | AI Query Reformulation",
  description: "Hybrid BM25 + Vector Search with AI Cross-Encoder Reranking and Grounded Answer Synthesis",
};

export default function SearchPage() {
  return (
    <Suspense fallback={<SearchSkeleton />}>
      <SearchContainer />
    </Suspense>
  );
}
