"use client";

import React from "react";
import { CheckCircle2, AlertCircle, Info, X } from "lucide-react";
import { cn } from "@/lib/utils";

export type ToastType = "success" | "error" | "info" | "warning";

interface ToastProps {
  type: ToastType;
  title: string;
  message?: string;
  onClose: () => void;
}

export const Toast: React.FC<ToastProps> = ({
  type,
  title,
  message,
  onClose,
}) => {
  return (
    <div
      className={cn(
        "flex items-start justify-between p-3.5 rounded-xl border shadow-2xl backdrop-blur-xl transition-all duration-200 animate-in slide-in-from-bottom-3",
        type === "success" && "border-emerald-500/30 bg-emerald-950/90 text-emerald-100",
        type === "error" && "border-rose-500/30 bg-rose-950/90 text-rose-100",
        type === "info" && "border-blue-500/30 bg-slate-900/90 text-slate-100",
        type === "warning" && "border-amber-500/30 bg-amber-950/90 text-amber-100"
      )}
    >
      <div className="flex items-start gap-2.5">
        {type === "success" && <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />}
        {type === "error" && <AlertCircle className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />}
        {type === "info" && <Info className="h-5 w-5 text-blue-400 shrink-0 mt-0.5" />}
        {type === "warning" && <AlertCircle className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />}

        <div>
          <div className="text-xs font-bold">{title}</div>
          {message && <p className="text-[11px] opacity-80 mt-0.5 leading-snug">{message}</p>}
        </div>
      </div>

      <button
        onClick={onClose}
        className="p-1 rounded-lg hover:bg-black/20 text-current opacity-70 hover:opacity-100 transition-opacity ml-3"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  );
};
