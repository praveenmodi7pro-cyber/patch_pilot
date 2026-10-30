"use client"

import React, { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import {
  FolderGit2,
  Play,
  FileCode2,
  Bug as BugIcon,
  Wrench,
  CheckCircle2,
  Clock,
  ArrowRight,
  Loader2,
  FileText,
  AlertTriangle,
  ChevronRight,
  GitBranch,
} from "lucide-react"
import Sidebar from "@/components/Sidebar"
import { SeverityBadge, VerificationBadge } from "@/components/StatusBadge"
import { MonacoCodeEditor } from "@/components/MonacoCodeEditor"
import { api } from "@/services/api"
import { Project, FileTreeNode, Bug, Repair, ActivityLog } from "@/types"
import { formatDate } from "@/lib/utils"

export default function ProjectDetailsPage() {
  const params = useParams()
  const router = useRouter()
  const projectId = params.projectId as string

  const [project, setProject] = useState<Project | null>(null)
  const [activeTab, setActiveTab] = useState<"overview" | "files" | "bugs" | "repairs" | "tests" | "activity">("overview")
  const [fileTree, setFileTree] = useState<FileTreeNode[]>([])
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [fileContent, setFileContent] = useState<string>("")
  const [bugs, setBugs] = useState<Bug[]>([])
  const [repairs, setRepairs] = useState<Repair[]>([])
  const [activities, setActivities] = useState<ActivityLog[]>([])
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)

  useEffect(() => {
    async function loadData() {
      try {
        const p = await api.projects.get(projectId)
        setProject(p)

        const [tree, acts] = await Promise.all([
          api.projects.getFiles(projectId),
          api.stats.getActivity(),
        ])
        setFileTree(tree)
        setActivities(acts.filter((a) => a.project_id === projectId))

        // If files exist, select first python file
        if (tree.length > 0) {
          const findFirstFile = (nodes: FileTreeNode[]): string | null => {
            for (const n of nodes) {
              if (!n.is_directory) return n.path
              if (n.children) {
                const found = findFirstFile(n.children)
                if (found) return found
              }
            }
            return null
          }
          const first = findFirstFile(tree)
          if (first) {
            setSelectedFile(first)
            const c = await api.projects.getFileContent(projectId, first)
            setFileContent(c.content)
          }
        }
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [projectId])

  const handleSelectFile = async (path: string) => {
    setSelectedFile(path)
    try {
      const c = await api.projects.getFileContent(projectId, path)
      setFileContent(c.content)
    } catch {
      setFileContent("# Unable to load file content")
    }
  }

  const handleStartAnalysis = async () => {
    setAnalyzing(true)
    try {
      const analysis = await api.analysis.start(projectId)
      router.push(`/projects/${projectId}/analysis/${analysis.id}`)
    } catch (err: any) {
      alert(err.message || "Failed to start analysis.")
      setAnalyzing(false)
    }
  }

  if (loading) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary-light" />
      </div>
    )
  }

  if (!project) {
    return (
      <div className="p-8 text-center text-muted">
        Project not found.{" "}
        <Link href="/dashboard" className="text-primary-light underline">
          Return to Dashboard
        </Link>
      </div>
    )
  }

  return (
    <div className="flex min-h-[calc(100vh-4rem)] bg-background">
      <Sidebar />

      <main className="flex-1 p-6 sm:p-8 max-w-7xl space-y-6 overflow-y-auto">
        {/* HEADER */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border/60 pb-6">
          <div className="space-y-1.5">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-main tracking-tight">
                {project.name}
              </h1>
              <span className="rounded bg-secondary px-2.5 py-0.5 text-xs font-mono font-medium text-cyan border border-border">
                {project.language}
              </span>
              <span className="rounded bg-card px-2.5 py-0.5 text-xs font-mono text-muted border border-border">
                {project.source_type}
              </span>
            </div>
            <p className="text-sm text-muted">
              {project.description || "Uploaded source code repository"}
            </p>
          </div>

          <button
            onClick={handleStartAnalysis}
            disabled={analyzing}
            className="flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-primary/20 hover:bg-primary-hover transition shrink-0 disabled:opacity-50"
          >
            {analyzing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4 fill-white" />}
            <span>Start Analysis</span>
          </button>
        </div>

        {/* METRICS ROW */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="rounded-xl border border-border bg-card p-4">
            <span className="text-xs font-semibold text-muted uppercase">Detected Bugs</span>
            <p className="text-xl font-bold text-error mt-1">{project.detected_bugs_count || 0}</p>
          </div>
          <div className="rounded-xl border border-border bg-card p-4">
            <span className="text-xs font-semibold text-muted uppercase">Generated Patches</span>
            <p className="text-xl font-bold text-primary-light mt-1">{project.generated_patches_count || 0}</p>
          </div>
          <div className="rounded-xl border border-border bg-card p-4">
            <span className="text-xs font-semibold text-muted uppercase">Default Branch</span>
            <p className="text-sm font-mono font-bold text-main mt-1 flex items-center gap-1.5">
              <GitBranch className="h-3.5 w-3.5 text-cyan" />
              {project.repository_branch || "main"}
            </p>
          </div>
          <div className="rounded-xl border border-border bg-card p-4">
            <span className="text-xs font-semibold text-muted uppercase">Last Status</span>
            <p className="text-xs font-mono font-bold text-main mt-1 uppercase">
              {project.last_analysis_status || "Ready to Analyze"}
            </p>
          </div>
        </div>

        {/* TABS */}
        <div className="flex items-center gap-2 border-b border-border text-sm font-semibold">
          {[
            { id: "overview", label: "Overview", icon: FileText },
            { id: "files", label: "Files", icon: FileCode2 },
            { id: "activity", label: "Activity", icon: Clock },
          ].map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-4 py-2.5 border-b-2 transition ${
                  activeTab === tab.id
                    ? "border-primary text-primary-light"
                    : "border-transparent text-muted hover:text-main"
                }`}
              >
                <Icon className="h-4 w-4" />
                {tab.label}
              </button>
            )
          })}
        </div>

        {/* TAB 1: OVERVIEW */}
        {activeTab === "overview" && (
          <div className="space-y-6">
            <div className="rounded-xl border border-border bg-card p-6 space-y-4">
              <h3 className="text-base font-bold text-main">Repository Overview</h3>
              <p className="text-sm text-muted leading-relaxed">
                This project has been indexed and structured. Click <b>&quot;Start Analysis&quot;</b> to trigger the 8-stage AI debugging pipeline. The pipeline scans AST trees, runs static linter diagnostics, formulates root cause explanations, generates minimal unified diffs, and validates fixes in isolated sandboxes.
              </p>
              <div className="pt-2">
                <button
                  onClick={handleStartAnalysis}
                  className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-xs font-semibold text-white hover:bg-primary-hover transition"
                >
                  <Play className="h-3.5 w-3.5 fill-white" />
                  Launch Full Investigation Pipeline
                </button>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: FILES & CODE VIEWER */}
        {activeTab === "files" && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 h-[550px]">
            {/* File Tree Panel */}
            <div className="rounded-xl border border-border bg-card p-4 overflow-y-auto font-mono text-xs space-y-1">
              <p className="text-xs font-sans font-bold text-muted uppercase tracking-wider mb-2">
                Repository Files
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

            {/* Monaco Viewer Panel */}
            <div className="md:col-span-2 rounded-xl border border-border bg-card overflow-hidden flex flex-col">
              <div className="flex items-center justify-between border-b border-border bg-secondary px-4 py-2 text-xs font-mono text-muted">
                <span>{selectedFile || "Select a file to inspect source"}</span>
                <span>Read-Only</span>
              </div>
              <div className="flex-1 p-2 bg-[#0e1525]">
                <MonacoCodeEditor value={fileContent} language="python" readOnly={true} />
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: ACTIVITY */}
        {activeTab === "activity" && (
          <div className="rounded-xl border border-border bg-card p-6 space-y-4">
            <h3 className="text-base font-bold text-main">Audit Trail</h3>
            <div className="space-y-3">
              {activities.length === 0 ? (
                <p className="text-xs text-muted">No activity events recorded for this project.</p>
              ) : (
                activities.map((a) => (
                  <div key={a.id} className="flex items-start gap-3 border-b border-border/40 pb-3 last:border-0">
                    <span className="mt-1 h-2 w-2 rounded-full bg-cyan" />
                    <div>
                      <p className="text-xs font-medium text-main">{a.description}</p>
                      <span className="text-[10px] text-muted">{formatDate(a.created_at)}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </main>
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
          <div className="pl-4 border-l border-border/40 space-y-1">
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

