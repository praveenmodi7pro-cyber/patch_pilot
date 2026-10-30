"use client"

import React, { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import {
  UploadCloud,
  FolderGit2,
  GitBranch,
  ArrowRight,
  AlertCircle,
  FileCheck2,
  Loader2,
  Terminal,
  ShieldAlert,
  Sparkles,
  Play,
} from "lucide-react"
import Sidebar from "@/components/Sidebar"
import { api } from "@/services/api"

export default function NewProjectPage() {
  const router = useRouter()
  const [tab, setTab] = useState<"zip" | "github">("zip")
  
  // ZIP State
  const [zipFile, setZipFile] = useState<File | null>(null)
  const [projectName, setProjectName] = useState("")
  const [description, setDescription] = useState("")
  const [dragActive, setDragActive] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // GitHub State
  const [githubUrl, setGithubUrl] = useState("")
  const [branch, setBranch] = useState("main")

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0]
      if (!file.name.toLowerCase().endsWith(".zip")) {
        setError("Only .zip repository archives are supported.")
        return
      }
      setZipFile(file)
      if (!projectName) {
        setProjectName(file.name.replace(".zip", ""))
      }
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0]
      if (!file.name.toLowerCase().endsWith(".zip")) {
        setError("Only .zip repository archives are supported.")
        return
      }
      setZipFile(file)
      if (!projectName) {
        setProjectName(file.name.replace(".zip", ""))
      }
    }
  }

  const handleUploadZip = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!zipFile) {
      setError("Please select a ZIP file to upload.")
      return
    }

    setError(null)
    setUploading(true)

    try {
      const project = await api.projects.uploadZip(zipFile, projectName, description)
      router.push(`/projects/${project.id}`)
    } catch (err: any) {
      setError(err.message || "Failed to upload project.")
    } finally {
      setUploading(false)
    }
  }

  const handleImportGitHub = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!githubUrl.includes("github.com")) {
      setError("Please enter a valid GitHub repository URL.")
      return
    }

    setError(null)
    setUploading(true)

    try {
      const project = await api.projects.importGitHub(githubUrl, branch, projectName)
      router.push(`/projects/${project.id}`)
    } catch (err: any) {
      setError(err.message || "Failed to import from GitHub.")
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="flex min-h-[calc(100vh-4rem)] bg-background">
      <Sidebar />

      <main className="flex-1 p-6 sm:p-8 max-w-4xl space-y-8 overflow-y-auto">
        <div className="space-y-1 border-b border-border/60 pb-6">
          <h1 className="text-2xl sm:text-3xl font-extrabold text-main tracking-tight">
            Create Debugging Project
          </h1>
          <p className="text-sm text-muted">
            Upload your source code repository for automated inspection, root cause diagnosis, and verified repairs.
          </p>
        </div>

        <div className="rounded-xl border border-cyan/40 bg-cyan/10 p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <span className="text-xs font-bold text-cyan uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles className="h-3.5 w-3.5" />
              Don&apos;t have broken software to test?
            </span>
            <p className="text-xs text-muted">
              Load our pre-packaged broken Python project with 3 intentional bugs (syntax error, runtime zero-division, and discount logic failure).
            </p>
          </div>
          <button
            type="button"
            onClick={async () => {
              setUploading(true)
              try {
                const proj = await api.projects.loadSample()
                router.push(`/projects/${proj.id}`)
              } catch (err: any) {
                setError(err.message || "Failed to load sample.")
                setUploading(false)
              }
            }}
            disabled={uploading}
            className="flex items-center gap-2 rounded-lg bg-cyan px-4 py-2 text-xs font-semibold text-background hover:bg-cyan-light transition shrink-0 shadow-md font-mono"
          >
            {uploading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5 fill-current" />}
            <span>Load Broken Sample App (1-Click)</span>
          </button>
        </div>

        {/* METHOD TABS */}
        <div className="flex items-center gap-2 border-b border-border">
          <button
            onClick={() => setTab("zip")}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-semibold border-b-2 transition ${
              tab === "zip"
                ? "border-primary text-primary-light"
                : "border-transparent text-muted hover:text-main"
            }`}
          >
            <UploadCloud className="h-4 w-4" />
            ZIP Archive Upload
          </button>
          <button
            onClick={() => setTab("github")}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-semibold border-b-2 transition ${
              tab === "github"
                ? "border-primary text-primary-light"
                : "border-transparent text-muted hover:text-main"
            }`}
          >
            <FolderGit2 className="h-4 w-4" />
            GitHub Repository Import
          </button>
        </div>

        {/* METHOD A: ZIP UPLOAD */}
        {tab === "zip" && (
          <form onSubmit={handleUploadZip} className="space-y-6">
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              className={`relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-10 text-center transition cursor-pointer ${
                dragActive
                  ? "border-primary bg-primary/10"
                  : zipFile
                  ? "border-success/50 bg-success/5"
                  : "border-border bg-card/60 hover:border-muted/60"
              }`}
            >
              <input
                type="file"
                accept=".zip"
                onChange={handleFileChange}
                className="absolute inset-0 opacity-0 cursor-pointer"
              />

              {zipFile ? (
                <div className="space-y-2">
                  <FileCheck2 className="mx-auto h-12 w-12 text-success" />
                  <p className="text-base font-bold text-main">{zipFile.name}</p>
                  <p className="text-xs text-muted">
                    {(zipFile.size / (1024 * 1024)).toFixed(2)} MB — Ready for ingestion
                  </p>
                  <span className="inline-block text-xs text-primary-light underline">
                    Click or drop to replace archive
                  </span>
                </div>
              ) : (
                <div className="space-y-2">
                  <UploadCloud className="mx-auto h-12 w-12 text-muted/60" />
                  <p className="text-base font-semibold text-main">
                    Drag and drop your project ZIP file here
                  </p>
                  <p className="text-xs text-muted">
                    or click to browse your files (Max limit: 50MB)
                  </p>
                </div>
              )}
            </div>

            <div className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted uppercase">Project Name</label>
                <input
                  type="text"
                  required
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  placeholder="e.g. backend-api or broken-python-app"
                  className="w-full rounded-lg border border-border bg-secondary px-3.5 py-2.5 text-sm text-main placeholder-muted/60 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary transition"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted uppercase">Description (Optional)</label>
                <textarea
                  rows={2}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Notes about known failing tests or buggy components..."
                  className="w-full rounded-lg border border-border bg-secondary px-3.5 py-2 text-sm text-main placeholder-muted/60 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary transition"
                />
              </div>
            </div>

            <div className="rounded-xl border border-border bg-secondary/30 p-4 flex items-start gap-3 text-xs text-muted">
              <ShieldAlert className="h-4 w-4 text-cyan shrink-0 mt-0.5" />
              <span>
                <b>Safe Extraction Guarantee:</b> Path traversals, zip slip attacks, and nested binaries are strictly rejected. Application secrets are scrubbed before AI inspection.
              </span>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <Link
                href="/dashboard"
                className="rounded-lg px-4 py-2.5 text-sm font-semibold text-muted hover:text-main transition"
              >
                Cancel
              </Link>
              <button
                type="submit"
                disabled={uploading || !zipFile}
                className="flex items-center gap-2 rounded-lg bg-primary px-6 py-2.5 text-sm font-semibold text-white shadow-md hover:bg-primary-hover focus:outline-none transition disabled:opacity-50"
              >
                {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Upload & Inspect Project"}
                {!uploading && <ArrowRight className="h-4 w-4" />}
              </button>
            </div>
          </form>
        )}

        {/* METHOD B: GITHUB IMPORT */}
        {tab === "github" && (
          <form onSubmit={handleImportGitHub} className="space-y-6">
            <div className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted uppercase">GitHub Repository URL</label>
                <input
                  type="url"
                  required
                  value={githubUrl}
                  onChange={(e) => setGithubUrl(e.target.value)}
                  placeholder="https://github.com/organization/repository"
                  className="w-full rounded-lg border border-border bg-secondary px-3.5 py-2.5 text-sm text-main placeholder-muted/60 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary transition"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-muted uppercase">Target Branch</label>
                  <input
                    type="text"
                    required
                    value={branch}
                    onChange={(e) => setBranch(e.target.value)}
                    placeholder="main"
                    className="w-full rounded-lg border border-border bg-secondary px-3.5 py-2.5 text-sm text-main placeholder-muted/60 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary transition"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-muted uppercase">Project Alias (Optional)</label>
                  <input
                    type="text"
                    value={projectName}
                    onChange={(e) => setProjectName(e.target.value)}
                    placeholder="Auto-derived if blank"
                    className="w-full rounded-lg border border-border bg-secondary px-3.5 py-2.5 text-sm text-main placeholder-muted/60 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary transition"
                  />
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-border bg-secondary/30 p-4 flex items-start gap-3 text-xs text-muted">
              <ShieldAlert className="h-4 w-4 text-warning shrink-0 mt-0.5" />
              <span>
                <b>Repository Privacy:</b> PatchPilot requires read-only permissions to clone and analyze the code. Patches are never pushed to your remote repository without explicit approval.
              </span>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <Link
                href="/dashboard"
                className="rounded-lg px-4 py-2.5 text-sm font-semibold text-muted hover:text-main transition"
              >
                Cancel
              </Link>
              <button
                type="submit"
                disabled={uploading || !githubUrl}
                className="flex items-center gap-2 rounded-lg bg-primary px-6 py-2.5 text-sm font-semibold text-white shadow-md hover:bg-primary-hover focus:outline-none transition disabled:opacity-50"
              >
                {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Import Repository"}
                {!uploading && <ArrowRight className="h-4 w-4" />}
              </button>
            </div>
          </form>
        )}
      </main>
    </div>
  )
}

