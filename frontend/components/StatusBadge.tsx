import React from "react"
import { ShieldCheck, AlertTriangle, AlertCircle, Info, CheckCircle2, XCircle, Clock } from "lucide-react"
import { cn } from "@/lib/utils"

export function SeverityBadge({ severity }: { severity: string }) {
  const s = severity.toLowerCase()
  switch (s) {
    case "critical":
      return (
        <span className="inline-flex items-center gap-1 rounded-md bg-error/15 px-2 py-0.5 text-xs font-semibold text-error border border-error/30">
          <AlertCircle className="h-3 w-3" />
          Critical
        </span>
      )
    case "high":
      return (
        <span className="inline-flex items-center gap-1 rounded-md bg-warning/15 px-2 py-0.5 text-xs font-semibold text-warning border border-warning/30">
          <AlertTriangle className="h-3 w-3" />
          High
        </span>
      )
    case "medium":
      return (
        <span className="inline-flex items-center gap-1 rounded-md bg-cyan/15 px-2 py-0.5 text-xs font-semibold text-cyan border border-cyan/30">
          <Info className="h-3 w-3" />
          Medium
        </span>
      )
    case "low":
    case "informational":
    default:
      return (
        <span className="inline-flex items-center gap-1 rounded-md bg-muted/15 px-2 py-0.5 text-xs font-medium text-muted border border-border">
          <Info className="h-3 w-3" />
          {severity.charAt(0).toUpperCase() + severity.slice(1)}
        </span>
      )
  }
}

export function VerificationBadge({ status }: { status: string }) {
  const s = status.toUpperCase()
  switch (s) {
    case "VERIFIED":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-success/15 px-3 py-1 text-xs font-bold text-success border border-success/40 shadow-sm shadow-success/10">
          <CheckCircle2 className="h-3.5 w-3.5" />
          VERIFIED
        </span>
      )
    case "PARTIALLY_VERIFIED":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-warning/15 px-3 py-1 text-xs font-bold text-warning border border-warning/40 shadow-sm shadow-warning/10">
          <AlertTriangle className="h-3.5 w-3.5" />
          PARTIALLY VERIFIED
        </span>
      )
    case "FAILED":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-error/15 px-3 py-1 text-xs font-bold text-error border border-error/40 shadow-sm shadow-error/10">
          <XCircle className="h-3.5 w-3.5" />
          FAILED
        </span>
      )
    case "INCONCLUSIVE":
    default:
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-muted/20 px-3 py-1 text-xs font-bold text-muted border border-border">
          <Clock className="h-3.5 w-3.5" />
          INCONCLUSIVE
        </span>
      )
  }
}

export function StageBadge({ stage }: { stage: string }) {
  const isFinished = stage === "COMPLETED"
  const isFailed = stage === "FAILED" || stage === "CANCELLED"

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-mono font-medium border",
        isFinished
          ? "bg-success/10 text-success border-success/30"
          : isFailed
          ? "bg-error/10 text-error border-error/30"
          : "bg-primary/10 text-primary-light border-primary/30 animate-pulse"
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", isFinished ? "bg-success" : isFailed ? "bg-error" : "bg-primary-light")} />
      {stage.replace(/_/g, " ")}
    </span>
  )
}

