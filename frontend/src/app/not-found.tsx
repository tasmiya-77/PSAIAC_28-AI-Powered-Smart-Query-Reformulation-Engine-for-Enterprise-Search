import React from "react";
import Link from "next/link";
import { Cpu, ArrowLeft, Search } from "lucide-react";
import { Button } from "@/components/ui/Button";

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-[#0b0f19] text-slate-100 p-6 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 shadow-2xl mb-6">
        <Cpu className="h-8 w-8 text-white" />
      </div>

      <div className="space-y-2">
        <span className="text-sm font-mono font-bold text-blue-400">404 ERROR</span>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
          Page Not Found
        </h1>
        <p className="text-sm text-slate-400 max-w-md mx-auto leading-relaxed">
          The route you are looking for does not exist or has been moved within the Query Reformulation Engine architecture.
        </p>
      </div>

      <div className="flex items-center space-x-3 mt-8">
        <Link href="/">
          <Button variant="primary" size="md" className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back to Dashboard
          </Button>
        </Link>
        <Link href="/search">
          <Button variant="outline" size="md" className="gap-2">
            <Search className="h-4 w-4" />
            Search Workbench
          </Button>
        </Link>
      </div>
    </div>
  );
}
