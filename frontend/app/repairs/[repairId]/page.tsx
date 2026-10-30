"use client"

import React, { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import {
  FileDiff,
  CheckCircle2,
  XCircle,
  RotateCcw,
  Play,
  Download,
  ArrowRight,
  Loader2,
  Sparkles,
  FileCode2,
  Terminal,
  ShieldCheck,
} from "lucide-react"
import Sidebar from "@/components/Sidebar"
import { MonacoDiffViewer } from "@/components/MonacoCodeEditor"
import { api } from "@/services/api"
import { Repair, RepairDiff } from "@/types"
import { formatDate } from "@/lib/utils"

export default function PatchReviewPage() {
  const params = useParams()
  const router = useRouter()
  const repairId = params.repairId as string

  const [repair, setRepair] = useState<Repair | null>(null)
  const [diff, setDiff] = useState<RepairDiff | null>(null)
  const [activeFileIndex, setActiveFileIndex] = useState(0)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)

  useEffect(() => {
    async function loadRepair() {
      try {
        const [r, d] = await Promise.all([
          api.repairs.get(repairId),
          api.repairs.getDiff(repairId),
        ])
        setRepair(r)
        setDiff(d)
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    loadRepair()
  }, [repairId])

  const handleApprove = async () => {
    setActionLoading(true)
    try {
      const updated = await api.repairs.approve(repairId)
      setRepair(updated)
    } catch (err: any) {
      alert(err.message || "Failed to approve patch.")
    } finally {
      setActionLoading(false)
    }
  }

  const handleReject = async () => {
    setActionLoading(true)
    try {
      const updated = await api.repairs.reject(repairId)
      setRepair(updated)
    } catch (err: any) {
      alert(err.message || "Failed to reject patch.")
    } finally {
      setActionLoading(false)
    }
  }

  const handleApply = async () => {
    setActionLoading(true)
    try {
      const updated = await api.repairs.apply(repairId)
      setRepair(updated)
      alert("Patch successfully applied in isolated sandbox workspace.")
    } catch (err: any) {
      alert(err.message || "Failed to apply patch.")
    } finally {
      setActionLoading(false)
    }
  }

  const handleRegenerate = async () => {
    setActionLoading(true)
    try {
      const updated = await api.repairs.regenerate(repairId)
      const newDiff = await api.repairs.getDiff(repairId)
      setRepair(updated)
      setDiff(newDiff)
    } catch (err: any) {
      alert(err.message || "Failed to regenerate patch.")
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary-light" />
      </div>
    )
  }

  if (!repair || !diff) {
    return (
      <div className="p-8 text-center text-muted">
        Repair not found.{" "}
        <Link href="/dashboard" className="text-primary-light underline">
          Return to Dashboard
        </Link>
      </div>
    )
  }

  const currentFile = diff.files[activeFileIndex] || { original_code: "", modified_code: "", path: "" }

  return (
    <div className="flex min-h-[calc(100vh-4rem)] bg-background">
      <Sidebar />

      <main className="flex-1 p-6 sm:p-8 max-w-7xl space-y-6 overflow-y-auto">
        {/* HEADER & ACTIONS */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border/60 pb-6">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-main tracking-tight flex items-center gap-2.5">
                <FileDiff className="h-7 w-7 text-primary-light" />
                Patch Review &amp; Code Diff
              </h1>
              <span className="rounded-full bg-secondary px-2.5 py-0.5 text-xs font-mono capitalize border border-border text-cyan">
                Status: {repair.status}
              </span>
            </div>
            <p className="text-xs text-muted">
              Generated: {formatDate(repair.created_at)} | Target: {diff.files.map((f) => f.path).join(", ")}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 shrink-0">
            <a
              href={api.repairs.getDownloadUrl(repair.id)}
              download
              className="flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-2 text-xs font-semibold text-main hover:bg-secondary transition"
            >
              <Download className="h-3.5 w-3.5" />
              Download .patch
            </a>

            <button
              onClick={handleRegenerate}
              disabled={actionLoading}
              className="flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-2 text-xs font-semibold text-muted hover:text-main hover:bg-secondary transition disabled:opacity-50"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              Regenerate
            </button>

            <button
              onClick={handleReject}
              disabled={actionLoading || repair.status === "rejected"}
              className="flex items-center gap-1.5 rounded-lg border border-error/30 bg-error/10 px-3 py-2 text-xs font-semibold text-error hover:bg-error/20 transition disabled:opacity-50"
            >
              <XCircle className="h-3.5 w-3.5" />
              Reject
            </button>

            <button
              onClick={handleApprove}
              disabled={actionLoading || repair.status === "approved"}
              className="flex items-center gap-1.5 rounded-lg bg-success px-3.5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-success/90 transition disabled:opacity-50"
            >
              <CheckCircle2 className="h-3.5 w-3.5" />
              Approve Patch
            </button>

            <Link
              href={`/repairs/${repair.id}/tests`}
              className="flex items-center gap-1.5 rounded-lg bg-primary px-3.5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-primary-hover transition"
            >
              <Play className="h-3.5 w-3.5 fill-white" />
              Run Sandbox Tests
            </Link>

            <Link
              href={`/repairs/${repair.id}/report`}
              className="flex items-center gap-1.5 rounded-lg border border-cyan/40 bg-cyan/15 px-3.5 py-2 text-xs font-semibold text-cyan hover:bg-cyan/25 transition"
            >
              <span>Audit Report</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>

        {/* MODIFICATION EXPLANATION CARD */}
        <div className="rounded-xl border border-border bg-card p-5 space-y-2">
          <h3 className="text-xs font-bold text-muted uppercase tracking-wider flex items-center gap-2">
            <Sparkles className="h-3.5 w-3.5 text-cyan" />
            AI Repair Explanation &amp; Rationale
          </h3>
          <p className="text-sm text-main leading-relaxed">
            {repair.explanation || "Minimal patch synthesized to repair root cause error while preserving existing structure."}
          </p>
        </div>

        {/* FILE SELECTION TABS */}
        {diff.files.length > 1 && (
          <div className="flex items-center gap-2 border-b border-border text-xs font-mono">
            {diff.files.map((file, idx) => (
              <button
                key={file.path}
                onClick={() => setActiveFileIndex(idx)}
                className={`flex items-center gap-1.5 px-3 py-2 border-b-2 transition ${
                  activeFileIndex === idx
                    ? "border-primary text-primary-light font-bold"
                    : "border-transparent text-muted hover:text-main"
                }`}
              >
                <FileCode2 className="h-3.5 w-3.5" />
                <span>{file.path}</span>
              </button>
            ))}
          </div>
        )}

        {/* MONACO SIDE-BY-SIDE DIFF VIEWER */}
        <div className="rounded-xl border border-border bg-card overflow-hidden">
          <div className="flex items-center justify-between border-b border-border bg-secondary px-4 py-2 text-xs font-mono text-muted">
            <div className="flex items-center gap-4">
              <span className="text-error font-semibold">- Original Repository File</span>
              <span className="text-success font-semibold">+ Proposed Patched File</span>
            </div>
            <span className="text-muted/80">{currentFile.path}</span>
          </div>

          <div className="p-1">
            <MonacoDiffViewer
              original={currentFile.original_code || repair.patch_content}
              modified={currentFile.modified_code || repair.patch_content}
              language="python"
              height="550px"
            />
          </div>
        </div>

        {/* RAW UNIFIED DIFF COLLAPSIBLE */}
        <div className="rounded-xl border border-border bg-card p-4 space-y-2">
          <h4 className="text-xs font-mono font-bold text-muted uppercase">Raw Unified Diff</h4>
          <pre className="rounded-lg bg-secondary p-3 font-mono text-xs text-muted overflow-x-auto whitespace-pre">
            {repair.patch_content}
          </pre>
        </div>
      </main>
    </div>
  )
}

