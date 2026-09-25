"use client";

import React, { useState, useEffect } from "react";
import { ShieldCheck, RefreshCw, Cpu, Users, Activity } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/context/ToastContext";
import { apiClient } from "@/lib/api-client";

export const AdminContainer: React.FC = () => {
  const { success, error: toastError } = useToast();
  const [status, setStatus] = useState<any>(null);
  const [isReindexing, setIsReindexing] = useState(false);

  const fetchStatus = async () => {
    try {
      const data = await apiClient.getAdminSystemStatus();
      setStatus(data);
    } catch {}
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleReindex = async () => {
    setIsReindexing(true);
    try {
      const data = await apiClient.reindexCollection();
      success("Re-index Complete", data.message);
      fetchStatus();
    } catch (err: any) {
      toastError("Re-index Failed", err.message || "Failed to re-index collection.");
    } finally {
      setIsReindexing(false);
    }
  };

  return (
    <div className="space-y-6 pb-8">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            <ShieldCheck className="h-6 w-6 text-amber-500" />
            Admin & System Diagnostics
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            ChromaDB vector collection management, user access control, and API telemetry logs.
          </p>
        </div>
        <Button
          onClick={handleReindex}
          disabled={isReindexing}
          variant="outline"
          size="sm"
          className="gap-2"
          aria-label="Trigger vector collection re-index"
        >
          <RefreshCw className={`h-4 w-4 ${isReindexing ? "animate-spin" : ""}`} />
          <span>Re-index Vector Collection</span>
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Health */}
        <Card variant="glass">
          <CardHeader>
            <CardTitle className="text-base font-bold flex items-center gap-2">
              <Cpu className="h-4 w-4 text-blue-400" />
              Engine System Diagnostics
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-200 dark:border-slate-800">
              <span className="text-slate-500 dark:text-slate-400">Application Name:</span>
              <span className="font-semibold text-slate-800 dark:text-slate-200">{status?.app_name || "Smart Query Engine"}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-200 dark:border-slate-800">
              <span className="text-slate-500 dark:text-slate-400">Environment:</span>
              <Badge variant="default" className="text-[10px]">{status?.environment || "development"}</Badge>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-200 dark:border-slate-800">
              <span className="text-slate-500 dark:text-slate-400">Gemini Model:</span>
              <span className="font-mono text-indigo-500 font-semibold">{status?.gemini_model || "gemini-2.5-flash"}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-200 dark:border-slate-800">
              <span className="text-slate-500 dark:text-slate-400">ChromaDB Status:</span>
              <span className="font-semibold text-emerald-500">{status?.chromadb_status?.status || "healthy"}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500 dark:text-slate-400">Cache Size:</span>
              <span className="font-mono text-slate-800 dark:text-slate-200">{status?.cache_items_count || 0} items cached</span>
            </div>
          </CardContent>
        </Card>

        {/* User Roles */}
        <Card variant="glass">
          <CardHeader>
            <CardTitle className="text-base font-bold flex items-center gap-2">
              <Users className="h-4 w-4 text-emerald-400" />
              User Access Control
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {(status?.users || []).map((u: any, idx: number) => (
              <div key={idx} className="flex items-center justify-between p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-100/60 dark:bg-slate-900/40 text-xs">
                <div>
                  <div className="font-semibold text-slate-800 dark:text-slate-200">{u.username}</div>
                  <div className="text-[11px] text-slate-500">{u.email}</div>
                </div>
                <Badge variant={u.role === "Admin" ? "success" : "outline"} className="text-[10px]">{u.role}</Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* API Telemetry Logs */}
      <Card variant="glass">
        <CardHeader>
          <CardTitle className="text-base font-bold flex items-center gap-2">
            <Activity className="h-4 w-4 text-indigo-400" />
            API Usage & Telemetry Audit Trail
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-xs">
            {(status?.api_usage_logs || []).map((l: any, idx: number) => (
              <div key={idx} className="flex items-center justify-between p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-100 dark:bg-slate-950 font-mono">
                <div className="flex items-center space-x-3">
                  <span className="text-slate-500">{l.timestamp}</span>
                  <span className="text-blue-500">{l.endpoint}</span>
                </div>
                <div className="flex items-center space-x-3">
                  <span className="text-emerald-500 font-semibold">{l.status_code} OK</span>
                  <span className="text-slate-400">{l.latency_ms}ms</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
