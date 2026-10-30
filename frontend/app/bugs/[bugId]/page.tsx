"use client"

import React, { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import {
  Bug as BugIcon,
  AlertCircle,
  Wrench,
  CheckCircle2,
  XCircle,
  FileCode2,
  ArrowLeft,
  Loader2,
  Sparkles,
  ShieldAlert,
  ArrowRight,
} from "lucide-react"
import Sidebar from "@/components/Sidebar"
import { SeverityBadge } from "@/components/StatusBadge"
import { MonacoCodeEditor } from "@/components/MonacoCodeEditor"
import { api } from "@/services/api"
import { Bug, Repair } from "@/types"

export default function BugDetailsPage() {
  const params = useParams()
  const router = useRouter()
  const bugId = params.bugId as string

  const [bug, setBug] = useState<Bug | null>(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [fileCode, setFileCode] = useState<string>("")

  useEffect(() => {
    async function loadBug() {
      try {
        const b = await api.bugs.get(bugId)
        setBug(b)

        // Try to fetch file source code
        // We can get project ID through analysis if needed or show evidence
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    loadBug()
  }, [bugId])

  const handleGenerateRepair = async () => {
    if (!bug) return
    setGenerating(true)
    try {
      const repair = await api.bugs.generateRepair(bug.id)
      router.push(`/repairs/${repair.id}`)
    } catch (err: any) {
      alert(err.message || "Failed to generate patch.")
      setGenerating(false)
    }
  }

  const handleUpdateStatus = async (status: string) => {
    if (!bug) return
    try {
      const updated = await api.bugs.updateStatus(bug.id, status)
      setBug(updated)
    } catch (err: any) {
      alert(err.message || "Failed to update bug status.")
    }
  }

  if (loading) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary-light" />
      </div>
    )
  }

  if (!bug) {
    return (
      <div className="p-8 text-center text-muted">
        Bug not found.{" "}
        <Link href="/dashboard" className="text-primary-light underline">
          Return to Dashboard
        </Link>
      </div>
    )
  }

  return (
    <div className="flex min-h-[calc(100vh-4rem)] bg-background">
      <Sidebar />

      <main className="flex-1 p-6 sm:p-8 max-w-5xl space-y-8 overflow-y-auto">
        {/* TOP BREADCRUMB & BACK */}
        <div className="flex items-center justify-between border-b border-border/60 pb-4">
          <button
            onClick={() => router.back()}
            className="flex items-center gap-1.5 text-xs text-muted hover:text-main font-semibold transition"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to Analysis
          </button>

          <div className="flex items-center gap-2">
            <span className="font-mono text-xs text-muted">ID: {bug.id.slice(0, 8)}</span>
            <span className="rounded bg-card px-2.5 py-0.5 text-xs font-mono text-muted border border-border">
              {bug.category}
            </span>
          </div>
        </div>

        {/* HEADER & ACTIONS */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <SeverityBadge severity={bug.severity} />
              <span className="rounded-full bg-secondary px-2.5 py-0.5 text-xs font-mono text-cyan border border-border">
                Confidence: {Math.round(bug.confidence * 100)}%
              </span>
              <span className="rounded-full bg-card px-2.5 py-0.5 text-xs font-mono text-muted border border-border capitalize">
                Status: {bug.status}
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-main tracking-tight">
              {bug.title}
            </h1>
            <p className="font-mono text-xs text-primary-light">
              {bug.file_path}:{bug.line_number || 1}
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <button
              onClick={() => handleUpdateStatus("reviewed")}
              className="rounded-lg border border-border bg-card px-3.5 py-2 text-xs font-semibold text-main hover:bg-secondary transition"
            >
              Mark Reviewed
            </button>
            <button
              onClick={() => handleUpdateStatus("dismissed")}
              className="rounded-lg border border-border bg-card px-3.5 py-2 text-xs font-semibold text-muted hover:text-error transition"
            >
              Dismiss
            </button>
            <button
              onClick={handleGenerateRepair}
              disabled={generating}
              className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-xs font-semibold text-white shadow-md hover:bg-primary-hover transition disabled:opacity-50"
            >
              {generating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Wrench className="h-3.5 w-3.5" />}
              <span>Generate Patch</span>
            </button>
          </div>
        </div>

        {/* DIAGNOSIS DETAILS */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 space-y-6">
            {/* Root Cause Card */}
            <div className="rounded-xl border border-border bg-card p-6 space-y-3">
              <h3 className="text-sm font-bold text-main uppercase tracking-wider flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-cyan" />
                Root Cause Explanation
              </h3>
              <p className="text-sm text-muted leading-relaxed">
                {bug.root_cause || bug.description}
              </p>
            </div>

            {/* Evidence Card */}
            <div className="rounded-xl border border-border bg-card p-6 space-y-3">
              <h3 className="text-sm font-bold text-main uppercase tracking-wider flex items-center gap-2">
                <FileCode2 className="h-4 w-4 text-primary-light" />
                Observed Evidence &amp; Tracebacks
              </h3>
              {bug.evidence && bug.evidence.length > 0 ? (
                <div className="space-y-2">
                  {bug.evidence.map((ev, idx) => (
                    <div
                      key={idx}
                      className="rounded-lg border border-border bg-secondary/80 p-3 font-mono text-xs text-muted leading-relaxed"
                    >
                      {ev}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-muted">No raw traceback logged.</p>
              )}
            </div>
          </div>

          {/* SIDEBAR METRICS */}
          <div className="space-y-6">
            <div className="rounded-xl border border-border bg-card p-5 space-y-4">
              <h4 className="text-xs font-bold text-muted uppercase tracking-wider">
                Bug Attributes
              </h4>

              <div className="space-y-3 text-xs">
                <div>
                  <span className="text-muted/70 block">Target File</span>
                  <span className="font-mono font-semibold text-main truncate block mt-0.5">
                    {bug.file_path}
                  </span>
                </div>
                <div>
                  <span className="text-muted/70 block">Line Number</span>
                  <span className="font-mono font-semibold text-main block mt-0.5">
                    Line {bug.line_number || 1}
                  </span>
                </div>
                <div>
                  <span className="text-muted/70 block">Category</span>
                  <span className="font-mono font-semibold text-main capitalize block mt-0.5">
                    {bug.category.replace(/_/g, " ")}
                  </span>
                </div>
                <div>
                  <span className="text-muted/70 block">AI Confidence Score</span>
                  <span className="font-mono font-semibold text-cyan block mt-0.5">
                    {Math.round(bug.confidence * 100)}% (Heuristic &amp; Traceback)
                  </span>
                </div>
              </div>

              <div className="pt-4 border-t border-border/60">
                <button
                  onClick={handleGenerateRepair}
                  disabled={generating}
                  className="w-full flex items-center justify-center gap-2 rounded-lg bg-primary py-2 text-xs font-semibold text-white shadow-md hover:bg-primary-hover transition disabled:opacity-50"
                >
                  {generating ? <Loader2 className="h-3 w-3 animate-spin" /> : <Wrench className="h-3 w-3" />}
                  <span>Formulate Code Patch</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

