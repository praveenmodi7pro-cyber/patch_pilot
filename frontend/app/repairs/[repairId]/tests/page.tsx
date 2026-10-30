"use client"

import React, { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import {
  Play,
  CheckCircle2,
  XCircle,
  Clock,
  Terminal,
  AlertTriangle,
  ArrowRight,
  Loader2,
  ShieldCheck,
  RotateCcw,
} from "lucide-react"
import Sidebar from "@/components/Sidebar"
import { api } from "@/services/api"
import { TestExecution, Repair } from "@/types"
import { formatDate } from "@/lib/utils"

export default function TestResultsPage() {
  const params = useParams()
  const router = useRouter()
  const repairId = params.repairId as string

  const [repair, setRepair] = useState<Repair | null>(null)
  const [tests, setTests] = useState<TestExecution[]>([])
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)

  const loadData = async () => {
    try {
      const [r, tList] = await Promise.all([
        api.repairs.get(repairId),
        api.testing.listTests(repairId),
      ])
      setRepair(r)
      setTests(tList)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [repairId])

  const handleRunTests = async () => {
    setRunning(true)
    try {
      await api.testing.runTests(repairId)
      await loadData()
    } catch (err: any) {
      alert(err.message || "Failed to execute tests in sandbox.")
    } finally {
      setRunning(false)
    }
  }

  if (loading) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary-light" />
      </div>
    )
  }

  const latestTest = tests[0] || null

  return (
    <div className="flex min-h-[calc(100vh-4rem)] bg-background">
      <Sidebar />

      <main className="flex-1 p-6 sm:p-8 max-w-6xl space-y-8 overflow-y-auto">
        {/* HEADER */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border/60 pb-6">
          <div className="space-y-1">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-main tracking-tight flex items-center gap-2.5">
              <Terminal className="h-7 w-7 text-primary-light" />
              Automated Test Runner
            </h1>
            <p className="text-xs text-muted">
              Isolated Docker sandbox execution logs and regression analysis
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleRunTests}
              disabled={running}
              className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-xs font-semibold text-white shadow-md hover:bg-primary-hover transition disabled:opacity-50"
            >
              {running ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5 fill-white" />}
              <span>Re-run Sandbox Suite</span>
            </button>

            <Link
              href={`/repairs/${repairId}/report`}
              className="flex items-center gap-1.5 rounded-lg border border-cyan/40 bg-cyan/15 px-4 py-2 text-xs font-semibold text-cyan hover:bg-cyan/25 transition"
            >
              <span>View Audit Report</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>

        {/* METRICS SUMMARY */}
        {latestTest ? (
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
            <div className="rounded-xl border border-border bg-card p-4 space-y-1">
              <span className="text-xs font-semibold text-muted uppercase">Outcome</span>
              <p
                className={`text-lg font-bold capitalize ${
                  latestTest.status === "passed" ? "text-success" : "text-error"
                }`}
              >
                {latestTest.status.replace(/_/g, " ")}
              </p>
            </div>
            <div className="rounded-xl border border-border bg-card p-4 space-y-1">
              <span className="text-xs font-semibold text-muted uppercase">Total Tests</span>
              <p className="text-xl font-bold text-main">{latestTest.total_tests}</p>
            </div>
            <div className="rounded-xl border border-border bg-card p-4 space-y-1">
              <span className="text-xs font-semibold text-muted uppercase">Passed</span>
              <p className="text-xl font-bold text-success">{latestTest.passed_tests}</p>
            </div>
            <div className="rounded-xl border border-border bg-card p-4 space-y-1">
              <span className="text-xs font-semibold text-muted uppercase">Failed</span>
              <p className="text-xl font-bold text-error">{latestTest.failed_tests}</p>
            </div>
            <div className="rounded-xl border border-border bg-card p-4 space-y-1">
              <span className="text-xs font-semibold text-muted uppercase">Duration</span>
              <p className="text-xl font-bold text-main">{latestTest.execution_duration.toFixed(2)}s</p>
            </div>
          </div>
        ) : (
          <div className="rounded-xl border border-border bg-card p-8 text-center text-muted text-sm space-y-3">
            <p>No tests have been executed for this repair yet.</p>
            <button
              onClick={handleRunTests}
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-xs font-semibold text-white hover:bg-primary-hover transition"
            >
              <Play className="h-3 w-3 fill-white" />
              Run Pytest Now
            </button>
          </div>
        )}

        {/* TERMINAL / LOGS VIEWER */}
        {latestTest && (
          <div className="rounded-xl border border-border bg-[#0a0f1d] overflow-hidden">
            <div className="flex items-center justify-between border-b border-border bg-secondary px-4 py-2.5 text-xs font-mono text-muted">
              <span className="flex items-center gap-2 text-main font-semibold">
                <Terminal className="h-4 w-4 text-cyan" />
                Pytest Execution Output (stdout / stderr)
              </span>
              <span>Executed: {formatDate(latestTest.started_at)}</span>
            </div>

            <pre className="p-4 font-mono text-xs text-muted/90 overflow-x-auto whitespace-pre leading-relaxed max-h-[450px]">
              {latestTest.stdout || latestTest.stderr || "No stdout logged by runner."}
            </pre>
          </div>
        )}
      </main>
    </div>
  )
}

