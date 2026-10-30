"use client"

import React, { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import {
  FolderGit2,
  FileCode2,
  AlertCircle,
  CheckCircle2,
  Clock,
  ArrowRight,
  Loader2,
  ChevronRight,
  ShieldAlert,
  Terminal,
  RotateCcw,
  Sparkles,
  FileDiff,
  ExternalLink,
} from "lucide-react"
import { MonacoCodeEditor } from "@/components/MonacoCodeEditor"
import { SeverityBadge, StageBadge, VerificationBadge } from "@/components/StatusBadge"
import { api } from "@/services/api"
import { Analysis, Bug, FileTreeNode, Project, Repair } from "@/types"

const STAGES_ORDER = [
  "QUEUED",
  "REPOSITORY_SCANNING",
  "STATIC_CODE_ANALYSIS",
  "BUG_DETECTION",
  "PATCH_GENERATION",
  "PATCH_VALIDATION",
  "TEST_EXECUTION",
  "REGRESSION_CHECK",
  "VERIFICATION",
  "COMPLETED",
]

export default function AnalysisWorkspacePage() {
  const params = useParams()
  const router = useRouter()
  const projectId = params.projectId as string
  const analysisId = params.analysisId as string

  const [analysis, setAnalysis] = useState<Analysis | null>(null)
  const [currentStage, setCurrentStage] = useState<string>("QUEUED")
  const [progressPct, setProgressPct] = useState<number>(10)
  const [bugs, setBugs] = useState<Bug[]>([])
  const [fileTree, setFileTree] = useState<FileTreeNode[]>([])
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [fileContent, setFileContent] = useState<string>("")
  const [highlightLine, setHighlightLine] = useState<number | undefined>(undefined)
  const [activeRepairId, setActiveRepairId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  // 1. Initial Load & Polling Fallback
  useEffect(() => {
    async function loadInitial() {
      try {
        const [a, bList, tree] = await Promise.all([
          api.analysis.get(analysisId),
          api.analysis.getBugs(analysisId),
          api.projects.getFiles(projectId),
        ])
        setAnalysis(a)
        setCurrentStage(a.current_stage)
        setBugs(bList)
        setFileTree(tree)

        // If bugs exist, select first bug's file
        if (bList.length > 0) {
          const firstBug = bList[0]
          setSelectedFile(firstBug.file_path)
          setHighlightLine(firstBug.line_number || undefined)
          try {
            const fc = await api.projects.getFileContent(projectId, firstBug.file_path)
            setFileContent(fc.content)
          } catch {}
        }
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    loadInitial()
  }, [analysisId, projectId])

  // 2. Real-time Server-Sent Events (SSE) Listener
  useEffect(() => {
    let es: EventSource | null = null
    try {
      es = api.analysis.getEventSource(analysisId)

      es.addEventListener("STAGE_CHANGED", (e: any) => {
        try {
          const data = JSON.parse(e.data)
          if (data.stage) {
            setCurrentStage(data.stage)
            const idx = STAGES_ORDER.indexOf(data.stage)
            if (idx >= 0) {
              setProgressPct(Math.round(((idx + 1) / STAGES_ORDER.length) * 100))
            }
          }
        } catch {}
      })

      es.addEventListener("BUG_DETECTED", async (e: any) => {
        try {
          const bList = await api.analysis.getBugs(analysisId)
          setBugs(bList)
        } catch {}
      })

      es.addEventListener("PATCH_GENERATED", (e: any) => {
        try {
          const data = JSON.parse(e.data)
          if (data.repair_id) {
            setActiveRepairId(data.repair_id)
          }
        } catch {}
      })

      es.addEventListener("COMPLETED", async (e: any) => {
        try {
          const data = JSON.parse(e.data)
          setCurrentStage("COMPLETED")
          setProgressPct(100)
          if (data.repair_id) {
            setActiveRepairId(data.repair_id)
          }
        } catch {}
      })

      es.onerror = () => {
        // SSE fallback polling
        api.analysis.getStatus(analysisId).then((st) => {
          setCurrentStage(st.current_stage)
          setProgressPct(st.progress_percentage)
        }).catch(() => {})
      }
    } catch {}

    return () => {
      if (es) es.close()
    }
  }, [analysisId])

  const handleSelectFile = async (path: string, line?: number) => {
    setSelectedFile(path)
    setHighlightLine(line)
    try {
      const c = await api.projects.getFileContent(projectId, path)
      setFileContent(c.content)
    } catch {
      setFileContent("# Unable to load file content")
    }
  }

  if (loading) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary-light" />
      </div>
    )
  }

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] bg-background overflow-hidden">
      {/* TOP PROGRESS BAR */}
      <div className="border-b border-border bg-secondary/80 px-4 py-2.5 flex items-center justify-between text-xs">
        <div className="flex items-center gap-3">
          <Link href={`/projects/${projectId}`} className="text-muted hover:text-main transition font-semibold">
            &larr; Project View
          </Link>
          <span className="text-border">|</span>
          <div className="flex items-center gap-2 font-mono">
            <span className="text-muted">Current Stage:</span>
            <StageBadge stage={currentStage} />
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="w-36 bg-card rounded-full h-2 overflow-hidden border border-border">
            <div
              className="bg-gradient-to-r from-primary to-cyan h-full transition-all duration-500"
              style={{ width: `${progressPct}%` }}
            />
          </div>
          <span className="font-mono text-xs text-muted">{progressPct}%</span>

          {activeRepairId && (
            <Link
              href={`/repairs/${activeRepairId}`}
              className="flex items-center gap-1.5 rounded bg-primary px-2.5 py-1 text-xs font-semibold text-white shadow-sm hover:bg-primary-hover transition"
            >
              <span>Review Patch</span>
              <ArrowRight className="h-3 w-3" />
            </Link>
          )}

          {currentStage === "COMPLETED" && activeRepairId && (
            <Link
              href={`/repairs/${activeRepairId}/report`}
              className="flex items-center gap-1.5 rounded bg-success/20 border border-success/40 px-2.5 py-1 text-xs font-semibold text-success hover:bg-success/30 transition"
            >
              <span>Audit Report</span>
              <CheckCircle2 className="h-3 w-3" />
            </Link>
          )}
        </div>
      </div>

      {/* 3-PANEL WORKSPACE */}
      <div className="flex-1 grid grid-cols-12 divide-x divide-border overflow-hidden">
        {/* PANEL 1: REPOSITORY EXPLORER (Cols 1-2) */}
        <div className="col-span-2 bg-[#0a0f1d] p-3 overflow-y-auto space-y-1 font-mono text-xs">
          <p className="px-2 py-1 text-[11px] font-sans font-bold text-muted uppercase tracking-wider">
            Files Explorer
          </p>
          {fileTree.map((node) => (
            <RenderTreeNode
              key={node.path}
              node={node}
              selectedPath={selectedFile}
              onSelect={handleSelectFile}
            />
          ))}
        </div>

        {/* PANEL 2: CENTER MONACO CODE VIEWER (Cols 3-8) */}
        <div className="col-span-6 flex flex-col bg-[#0e1525] overflow-hidden">
          <div className="flex items-center justify-between border-b border-border bg-secondary/60 px-4 py-2 text-xs font-mono text-muted">
            <span className="truncate">{selectedFile || "Select a file to inspect"}</span>
            <span className="shrink-0">{highlightLine ? `Line: ${highlightLine}` : "Read-Only"}</span>
          </div>

          <div className="flex-1 p-1">
            <MonacoCodeEditor
              value={fileContent}
              language="python"
              readOnly={true}
              highlightLine={highlightLine}
            />
          </div>
        </div>

        {/* PANEL 3: AI INVESTIGATION DRAWER (Cols 9-12) */}
        <div className="col-span-4 bg-secondary/30 p-5 overflow-y-auto space-y-6">
          <div className="space-y-1 border-b border-border/60 pb-3">
            <h3 className="text-base font-bold text-main flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-cyan" />
              AI Investigation
            </h3>
            <p className="text-xs text-muted">
              Live diagnostics, root cause evidence, and patch status
            </p>
          </div>

          {/* ACTIVE STAGE TRACKER */}
          <div className="space-y-2">
            <span className="text-xs font-semibold text-muted uppercase tracking-wider">
              Pipeline Stage
            </span>
            <div className="rounded-xl border border-border bg-card p-3.5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-main">
                  {currentStage.replace(/_/g, " ")}
                </span>
                <span className="text-xs font-mono text-cyan">{progressPct}%</span>
              </div>
              <p className="text-xs text-muted leading-relaxed">
                {currentStage === "COMPLETED"
                  ? "Analysis and sandbox verification complete. Results persisted."
                  : currentStage === "TEST_EXECUTION"
                  ? "Running Pytest suite inside isolated sandbox..."
                  : currentStage === "PATCH_GENERATION"
                  ? "Formulating minimal unified diff repair..."
                  : "Scanning AST and verifying repository health..."}
              </p>
            </div>
          </div>

          {/* DETECTED BUGS LIST */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-muted uppercase tracking-wider">
                Detected Issues ({bugs.length})
              </span>
            </div>

            {bugs.length === 0 ? (
              <div className="rounded-xl border border-border/80 bg-card/60 p-5 text-center text-xs text-muted">
                {currentStage === "QUEUED" || currentStage === "REPOSITORY_SCANNING" ? (
                  <div className="flex flex-col items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin text-primary-light" />
                    <span>Investigating codebase...</span>
                  </div>
                ) : (
                  <span>No bugs detected in scanned files.</span>
                )}
              </div>
            ) : (
              <div className="space-y-3">
                {bugs.map((bug) => (
                  <div
                    key={bug.id}
                    onClick={() => handleSelectFile(bug.file_path, bug.line_number || undefined)}
                    className="cursor-pointer rounded-xl border border-border bg-card p-4 space-y-2.5 hover:border-primary/50 transition group"
                  >
                    <div className="flex items-center justify-between">
                      <SeverityBadge severity={bug.severity} />
                      <span className="font-mono text-[11px] text-muted">
                        Confidence: {Math.round(bug.confidence * 100)}%
                      </span>
                    </div>

                    <h4 className="text-sm font-bold text-main group-hover:text-primary-light transition">
                      {bug.title}
                    </h4>

                    <div className="font-mono text-xs text-muted/80 bg-secondary/70 p-2 rounded border border-border/40">
                      {bug.file_path}:{bug.line_number || 1}
                    </div>

                    {bug.root_cause && (
                      <p className="text-xs text-muted leading-relaxed">
                        {bug.root_cause}
                      </p>
                    )}

                    <div className="pt-2 flex items-center justify-between border-t border-border/40">
                      <Link
                        href={`/bugs/${bug.id}`}
                        onClick={(e) => e.stopPropagation()}
                        className="text-xs text-primary-light hover:underline flex items-center gap-1 font-semibold"
                      >
                        Inspect Full Diagnosis
                        <ChevronRight className="h-3 w-3" />
                      </Link>

                      {activeRepairId && (
                        <Link
                          href={`/repairs/${activeRepairId}`}
                          onClick={(e) => e.stopPropagation()}
                          className="text-xs text-cyan hover:underline flex items-center gap-1 font-semibold"
                        >
                          View Patch
                          <FileDiff className="h-3 w-3" />
                        </Link>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function RenderTreeNode({
  node,
  selectedPath,
  onSelect,
}: {
  node: FileTreeNode
  selectedPath: string | null
  onSelect: (path: string) => void
}) {
  const [open, setOpen] = useState(true)

  if (node.is_directory) {
    return (
      <div className="space-y-1">
        <button
          onClick={() => setOpen(!open)}
          className="flex w-full items-center gap-1.5 py-1 px-1.5 rounded hover:bg-secondary text-left text-muted font-semibold"
        >
          <ChevronRight className={`h-3 w-3 transition-transform ${open ? "rotate-90" : ""}`} />
          <span>{node.name}/</span>
        </button>
        {open && node.children && (
          <div className="pl-3 border-l border-border/40 space-y-1">
            {node.children.map((child) => (
              <RenderTreeNode
                key={child.path}
                node={child}
                selectedPath={selectedPath}
                onSelect={onSelect}
              />
            ))}
          </div>
        )}
      </div>
    )
  }

  const isSelected = selectedPath === node.path
  return (
    <button
      onClick={() => onSelect(node.path)}
      className={`flex w-full items-center gap-1.5 py-1 px-2 rounded text-left transition ${
        isSelected
          ? "bg-primary/20 text-primary-light font-semibold border border-primary/30"
          : "text-muted hover:text-main hover:bg-secondary"
      }`}
    >
      <FileCode2 className="h-3 w-3 shrink-0" />
      <span className="truncate">{node.name}</span>
    </button>
  )
}

