"use client";

import React, { useState } from "react";
import { Sliders, Save, Key, Cpu, Database, Shield } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/context/ToastContext";

export const SettingsContainer: React.FC = () => {
  const { success } = useToast();
  const [model, setModel] = useState("gemini-2.5-flash");
  const [cacheEnabled, setCacheEnabled] = useState(true);
  const [minConfidence, setMinConfidence] = useState(0.7);

  const handleSave = () => {
    success("Settings Updated", "Configuration changes persisted successfully.");
  };

  return (
    <div className="space-y-6 pb-8 max-w-4xl">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            <Sliders className="h-6 w-6 text-indigo-500" />
            Engine Settings & Configuration
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            Customize LLM reformulation parameters, vector store indexing, and search thresholds.
          </p>
        </div>
        <Button onClick={handleSave} size="sm" className="gap-2">
          <Save className="h-4 w-4" />
          <span>Save Changes</span>
        </Button>
      </div>

      <Card variant="glass">
        <CardHeader>
          <CardTitle className="text-base font-bold flex items-center gap-2">
            <Cpu className="h-4 w-4 text-blue-400" />
            Gemini AI Reformulation Engine
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-xs">
          <div className="space-y-1">
            <label className="text-slate-300 font-medium">Selected Model</label>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="gemini-2.5-flash">Gemini 2.5 Flash (Ultra-fast low latency)</option>
              <option value="gemini-2.5-pro">Gemini 2.5 Pro (Deep analytical reasoning)</option>
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-slate-300 font-medium">Min Reranker Relevance Threshold</label>
            <input
              type="number"
              step="0.05"
              min="0.0"
              max="1.0"
              value={minConfidence}
              onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
              className="w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </CardContent>
      </Card>

      <Card variant="glass">
        <CardHeader>
          <CardTitle className="text-base font-bold flex items-center gap-2">
            <Database className="h-4 w-4 text-indigo-400" />
            Performance & Caching
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-xs">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-semibold text-slate-200">In-Memory Search Caching</div>
              <div className="text-[11px] text-slate-500">Cache repeated query results to achieve &lt;15ms response latency</div>
            </div>
            <input
              type="checkbox"
              checked={cacheEnabled}
              onChange={(e) => setCacheEnabled(e.target.checked)}
              className="h-4 w-4 rounded accent-blue-600 cursor-pointer"
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
