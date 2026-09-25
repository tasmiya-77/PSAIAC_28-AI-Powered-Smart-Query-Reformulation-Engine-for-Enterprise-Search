import React from "react";
import { cn } from "@/lib/utils";

interface StatusIndicatorProps {
  status: "healthy" | "degraded" | "unavailable" | "loading";
  label?: string;
  className?: string;
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  label,
  className,
}) => {
  return (
    <div className={cn("inline-flex items-center gap-2 text-xs font-medium", className)}>
      <span className="relative flex h-2.5 w-2.5">
        <span
          className={cn(
            "absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping",
            status === "healthy" && "bg-emerald-400",
            status === "degraded" && "bg-amber-400",
            status === "unavailable" && "bg-rose-400",
            status === "loading" && "bg-blue-400"
          )}
        />
        <span
          className={cn(
            "relative inline-flex h-2.5 w-2.5 rounded-full",
            status === "healthy" && "bg-emerald-500",
            status === "degraded" && "bg-amber-500",
            status === "unavailable" && "bg-rose-500",
            status === "loading" && "bg-blue-500"
          )}
        />
      </span>
      {label && (
        <span
          className={cn(
            status === "healthy" && "text-emerald-400",
            status === "degraded" && "text-amber-400",
            status === "unavailable" && "text-rose-400",
            status === "loading" && "text-blue-400"
          )}
        >
          {label}
        </span>
      )}
    </div>
  );
};
