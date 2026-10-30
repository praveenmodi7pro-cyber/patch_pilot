"use client"

import React, { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Download,
  FileText,
  Clock,
  ArrowLeft,
  Loader2,
  Terminal,
  ExternalLink,
} from "lucide-react"
import Sidebar from "@/components/Sidebar"
import { VerificationBadge } from "@/components/StatusBadge"
import { api } from "@/services/api"
import { VerificationReport, Repair } from "@/types"
import { formatDate } from "@/lib/utils"

export default function VerificationReportPage() {
  const params = useParams()
  const router = useRouter()
  const repairId = params.repairId as string

  const [report, setReport] = useState<VerificationReport | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadReport() {
      try {
        const r = await api.reports.getReport(repairId)
        setReport(r)
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    loadReport()
  }, [repairId])

  if (loading) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary-light" />
      </div>
    )
  }

  if (!report) {
    return (
      <div className="p-8 text-center text-muted">
        Verification report not found for this repair.{" "}
        <Link href={`/repairs/${repairId}/tests`} className="text-primary-light underline">
          Run tests first
        </Link>
      </div>
    )
  }

  const c = (report.report_content || {}) as any
  const sec1 = c.section_1_original_issue || {}
  const sec2 = c.section_2_root_cause || {}
  const sec3 = c.section_3_files_affected || {}
  const sec4 = c.section_4_generated_patch || {}
  const sec5 = c.section_5_changes_applied || {}
  const sec6 = c.section_6_tests_executed || {}
  const sec7 = c.section_7_test_results || {}
  const sec8 = c.section_8_regression_checks || {}
  const sec9 = c.section_9_verification_decision || {}
  const sec10 = c.section_10_remaining_risks || {}
  const sec11 = c.section_11_recommended_next_action || {}

  return (
    <div className="flex min-h-[calc(100vh-4rem)] bg-background">
      <Sidebar />

      <main className="flex-1 p-6 sm:p-8 max-w-5xl space-y-8 overflow-y-auto">
        {/* TOP BAR */}
        <div className="flex items-center justify-between border-b border-border/60 pb-4">
          <button
            onClick={() => router.back()}
            className="flex items-center gap-1.5 text-xs text-muted hover:text-main font-semibold transition"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to Patch
          </button>

          <a
            href={api.reports.getPdfUrl(repairId)}
            download
            className="flex items-center gap-1.5 rounded-lg bg-primary px-3.5 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-primary-hover transition"
          >
            <Download className="h-3.5 w-3.5" />
            Export Official Audit PDF
          </a>
        </div>

        {/* VERIFICATION BANNER */}
        <div className="rounded-2xl border border-border bg-card p-6 sm:p-8 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-6">
          <div className="space-y-2">
            <span className="text-xs font-bold text-muted uppercase tracking-wider">
              Verification Audit Verdict
            </span>
            <div className="flex items-center gap-3">
              <VerificationBadge status={report.status} />
              <span className="font-mono text-xs text-muted">
                Audit ID: {report.id.slice(0, 8)}
              </span>
            </div>
            <p className="text-xs text-muted/80">
              Evaluated: {formatDate(report.created_at)} | Target: {sec1.title || "Automated Repair"}
            </p>
          </div>

          <div className="flex items-center gap-6 border-t sm:border-t-0 sm:border-l border-border/80 pt-4 sm:pt-0 sm:pl-6 text-xs font-mono">
            <div>
              <span className="text-muted/70 block">Checks Passed</span>
              <span className="text-base font-bold text-success">
                {report.checks_passed?.length || 0}
              </span>
            </div>
            <div>
              <span className="text-muted/70 block">Checks Failed</span>
              <span className="text-base font-bold text-error">
                {report.checks_failed?.length || 0}
              </span>
            </div>
          </div>
        </div>

        {/* 11-SECTION STRUCTURED REPORT */}
        <div className="space-y-6">
          {/* 1. Original Issue */}
          <div className="rounded-xl border border-border bg-card p-6 space-y-3">
            <h3 className="text-sm font-bold text-main uppercase tracking-wider flex items-center gap-2">
              <span className="font-mono text-cyan">1.</span>
              Original Issue &amp; Discovery
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div>
                <span className="text-muted/70 block">Bug Title</span>
                <span className="text-main font-semibold mt-0.5 block">{sec1.title}</span>
              </div>
              <div>
                <span className="text-muted/70 block">Affected File &amp; Line</span>
                <span className="font-mono text-main font-semibold mt-0.5 block">
                  {sec1.file_path}:{sec1.line_number || 1}
                </span>
              </div>
            </div>
            <p className="text-xs text-muted leading-relaxed mt-2">{sec1.description}</p>
          </div>

          {/* 2. Root Cause */}
          <div className="rounded-xl border border-border bg-card p-6 space-y-3">
            <h3 className="text-sm font-bold text-main uppercase tracking-wider flex items-center gap-2">
              <span className="font-mono text-cyan">2.</span>
              Root Cause Diagnosis
            </h3>
            <p className="text-sm text-main leading-relaxed">{sec2.root_cause}</p>
            <span className="inline-block text-xs font-mono text-muted">
              Diagnostic Confidence: {Math.round((sec2.confidence || 0.85) * 100)}%
            </span>
          </div>

          {/* 3 & 4. Files Affected & Patch */}
          <div className="rounded-xl border border-border bg-card p-6 space-y-3">
            <h3 className="text-sm font-bold text-main uppercase tracking-wider flex items-center gap-2">
              <span className="font-mono text-cyan">3 &amp; 4.</span>
              Synthesized Code Modification
            </h3>
            <p className="text-xs text-muted">{sec4.explanation}</p>
            <div className="font-mono text-xs text-main bg-secondary p-3 rounded border border-border/60 overflow-x-auto whitespace-pre">
              {sec4.patch_content}
            </div>
          </div>

          {/* 5, 6 & 7. Execution & Test Results */}
          <div className="rounded-xl border border-border bg-card p-6 space-y-3">
            <h3 className="text-sm font-bold text-main uppercase tracking-wider flex items-center gap-2">
              <span className="font-mono text-cyan">5, 6 &amp; 7.</span>
              Isolated Test Execution Results
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
              <div className="bg-secondary p-3 rounded border border-border">
                <span className="text-muted block">Runner</span>
                <span className="font-bold text-main">{sec6.runner || "Pytest"}</span>
              </div>
              <div className="bg-secondary p-3 rounded border border-border">
                <span className="text-muted block">Total Tests</span>
                <span className="font-bold text-main">{sec7.passed + sec7.failed}</span>
              </div>
              <div className="bg-secondary p-3 rounded border border-border">
                <span className="text-muted block">Passed</span>
                <span className="font-bold text-success">{sec7.passed}</span>
              </div>
              <div className="bg-secondary p-3 rounded border border-border">
                <span className="text-muted block">Failed</span>
                <span className="font-bold text-error">{sec7.failed}</span>
              </div>
            </div>
          </div>

          {/* 8. Regression Checks */}
          <div className="rounded-xl border border-border bg-card p-6 space-y-3">
            <h3 className="text-sm font-bold text-main uppercase tracking-wider flex items-center gap-2">
              <span className="font-mono text-cyan">8.</span>
              Regression Differential Check
            </h3>
            <div className="flex items-center gap-2 text-xs">
              <span className="text-muted">Regression Introduced:</span>
              <span
                className={`font-mono font-bold ${
                  sec8.has_regression ? "text-error" : "text-success"
                }`}
              >
                {sec8.has_regression ? "YES (WARNING)" : "ZERO REGRESSIONS (CLEAN)"}
              </span>
            </div>
          </div>

          {/* 9 & 10. Verification Decision & Remaining Risks */}
          <div className="rounded-xl border border-border bg-card p-6 space-y-3">
            <h3 className="text-sm font-bold text-main uppercase tracking-wider flex items-center gap-2">
              <span className="font-mono text-cyan">9 &amp; 10.</span>
              Verification Decision &amp; Outstanding Risks
            </h3>
            <div className="space-y-1.5">
              <p className="text-xs font-semibold text-muted">Checks Executed &amp; Passed:</p>
              <ul className="list-disc list-inside text-xs text-muted space-y-1">
                {(report.checks_passed || []).map((cp: string, idx: number) => (
                  <li key={idx} className="text-success">
                    {cp}
                  </li>
                ))}
              </ul>
            </div>
            {report.remaining_risks && report.remaining_risks.length > 0 && (
              <div className="pt-2 space-y-1.5">
                <p className="text-xs font-semibold text-warning">Remaining Risks Identified:</p>
                <ul className="list-disc list-inside text-xs text-muted space-y-1">
                  {report.remaining_risks.map((r: string, idx: number) => (
                    <li key={idx}>{r}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* 11. Recommended Next Action */}
          <div className="rounded-xl border border-border bg-card p-6 space-y-3">
            <h3 className="text-sm font-bold text-main uppercase tracking-wider flex items-center gap-2">
              <span className="font-mono text-cyan">11.</span>
              Recommended Next Action
            </h3>
            <p className="text-sm font-semibold text-main">{sec11.recommendation}</p>
            <p className="text-xs text-muted/70 italic">{sec11.note}</p>
          </div>
        </div>
      </main>
    </div>
  )
}
