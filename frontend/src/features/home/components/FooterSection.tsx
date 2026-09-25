"use client";

import React from "react";
import { Cpu, Globe, ExternalLink } from "lucide-react";
import { StatusIndicator } from "@/components/ui/StatusIndicator";

export const FooterSection: React.FC = () => {
  return (
    <footer className="mt-12 border-t border-slate-200 dark:border-slate-800/80 pt-8 pb-6 text-xs text-slate-500 space-y-6">
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Left branding */}
        <div className="flex items-center space-x-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white">
            <Cpu className="h-4 w-4" />
          </div>
          <div>
            <span className="font-bold text-slate-800 dark:text-slate-200">
              QueryReform AI Engine
            </span>
            <span className="text-[11px] text-slate-400 block sm:inline sm:ml-2">
              © 2026 Enterprise Edition. All rights reserved.
            </span>
          </div>
        </div>

        {/* Center links */}
        <div className="flex items-center space-x-4">
          <a href="/search" className="hover:text-blue-500 transition-colors">
            Search
          </a>
          <a href="/upload" className="hover:text-blue-500 transition-colors">
            Upload
          </a>
          <a href="/analytics" className="hover:text-blue-500 transition-colors">
            Analytics
          </a>
          <a href="/admin" className="hover:text-blue-500 transition-colors">
            Admin
          </a>
          <a href="/settings" className="hover:text-blue-500 transition-colors">
            Settings
          </a>
        </div>

        {/* Right status */}
        <div className="flex items-center gap-2">
          <Globe className="h-3.5 w-3.5 text-slate-400" />
          <StatusIndicator status="healthy" label="System Operational" />
        </div>
      </div>
    </footer>
  );
};
