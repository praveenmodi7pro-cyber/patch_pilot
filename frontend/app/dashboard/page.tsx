"use client"

import React, { useEffect, useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import {
  PlusCircle,
  FolderGit2,
  Bug,
  ShieldCheck,
  Clock,
  ArrowRight,
  Activity,
  CheckCircle2,
  AlertTriangle,
  Play,
  Loader2,
  Sparkles,
} from "lucide-react"
import Sidebar from "@/components/Sidebar"
import { api } from "@/services/api"
import { Project, DashboardStats, ActivityLog, User } from "@/types"
import { formatDate } from "@/lib/utils"

export default function DashboardPage() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [projects, setProjects] = useState<Project[]>([])
  const [activities, setActivities] = useState<ActivityLog[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadDashboard() {
      try {
        const u = await api.auth.getMe()
        setUser(u)

        const [s, p, a] = await Promise.all([
          api.stats.getDashboardStats(),
          api.projects.list(),
          api.stats.getActivity(),
        ])
        setStats(s)
        setProjects(p)
        setActivities(a)
      } catch (err) {
        // Not authenticated -> redirect to login
        router.push("/login")
      } finally {
        setLoading(false)
      }
    }
    loadDashboard()
  }, [router])

  if (loading) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3 text-muted">
          <Loader2 className="h-8 w-8 animate-spin text-primary-light" />
          <span className="text-sm font-mono">Loading telemetry and repositories...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-[calc(100vh-4rem)] bg-background">
      <Sidebar />

      <main className="flex-1 p-6 sm:p-8 max-w-7xl space-y-8 overflow-y-auto">
        {/* HEADER */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border/60 pb-6">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-main tracking-tight">
              Engineering Console
            </h1>
            <p className="text-sm text-muted mt-1">
              Welcome back, <span className="font-semibold text-main">{user?.name}</span>. Real-time project diagnostics and verified repairs.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={async () => {
                try {
                  const proj = await api.projects.loadSample()
                  router.push(`/projects/${proj.id}`)
                } catch (err: any) {
                  alert(err.message || "Failed to load sample.")
                }
              }}
              className="flex items-center gap-1.5 rounded-lg border border-cyan/40 bg-cyan/10 px-3.5 py-2.5 text-xs font-semibold text-cyan hover:bg-cyan/20 transition shrink-0"
            >
              <Sparkles className="h-3.5 w-3.5" />
              <span>Load Broken Sample App</span>
            </button>

            <Link
              href="/projects/new"
              className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-white shadow-md hover:bg-primary-hover transition shrink-0"
            >
              <PlusCircle className="h-4 w-4" />
              <span>New Debugging Session</span>
            </Link>
          </div>
        </div>

        {/* REAL DATABASE-DERIVED STATS */}
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          <div className="rounded-xl border border-border bg-card p-5 space-y-1">
            <span className="text-xs font-semibold text-muted uppercase">Total Projects</span>
            <p className="text-2xl font-bold text-main">{stats?.total_projects ?? 0}</p>
            <span className="text-[11px] text-muted/80">Active repositories</span>
          </div>

          <div className="rounded-xl border border-border bg-card p-5 space-y-1">
            <span className="text-xs font-semibold text-muted uppercase">Debugging Runs</span>
            <p className="text-2xl font-bold text-main">{stats?.total_debugging_sessions ?? 0}</p>
            <span className="text-[11px] text-muted/80">Full pipeline executions</span>
          </div>

          <div className="rounded-xl border border-border bg-card p-5 space-y-1">
            <span className="text-xs font-semibold text-muted uppercase">Bugs Detected</span>
            <p className="text-2xl font-bold text-error">{stats?.bugs_detected ?? 0}</p>
            <span className="text-[11px] text-muted/80">Identified root causes</span>
          </div>

          <div className="rounded-xl border border-border bg-card p-5 space-y-1">
            <span className="text-xs font-semibold text-muted uppercase">Repairs Verified</span>
            <p className="text-2xl font-bold text-success">{stats?.repairs_verified ?? 0}</p>
            <span className="text-[11px] text-muted/80">Passed sandbox tests</span>
          </div>

          <div className="rounded-xl border border-border bg-card p-5 space-y-1">
            <span className="text-xs font-semibold text-muted uppercase">Awaiting Review</span>
            <p className="text-2xl font-bold text-warning">{stats?.repairs_awaiting_review ?? 0}</p>
            <span className="text-[11px] text-muted/80">Patches ready for inspect</span>
          </div>
        </div>

        {/* RECENT PROJECTS & RECENT ACTIVITY */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* PROJECTS LIST (Col span 2) */}
          <div id="projects" className="lg:col-span-2 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-main flex items-center gap-2">
                <FolderGit2 className="h-4 w-4 text-primary-light" />
                Repositories &amp; Projects
              </h2>
              <span className="text-xs text-muted">{projects.length} repositories indexed</span>
            </div>

            {projects.length === 0 ? (
              <div className="rounded-xl border border-dashed border-border bg-card/40 p-12 text-center space-y-3">
                <FolderGit2 className="mx-auto h-10 w-10 text-muted/40" />
                <h3 className="text-sm font-semibold text-main">No projects uploaded yet</h3>
                <p className="text-xs text-muted max-w-sm mx-auto">
                  Upload a ZIP archive of a broken Python repository or connect GitHub to initiate autonomous AI root cause analysis.
                </p>
                <div className="pt-2 flex items-center justify-center gap-3">
                  <button
                    onClick={async () => {
                      try {
                        const proj = await api.projects.loadSample()
                        router.push(`/projects/${proj.id}`)
                      } catch (err: any) {
                        alert(err.message || "Failed to load sample.")
                      }
                    }}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-cyan/40 bg-cyan/15 px-3.5 py-2 text-xs font-semibold text-cyan hover:bg-cyan/25 transition"
                  >
                    <Sparkles className="h-3.5 w-3.5" />
                    Load Built-in Broken App (1-Click)
                  </button>
                  <Link
                    href="/projects/new"
                    className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3.5 py-2 text-xs font-semibold text-white hover:bg-primary-hover transition"
                  >
                    <PlusCircle className="h-3.5 w-3.5" />
                    Upload Custom ZIP
                  </Link>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                {projects.map((proj) => (
                  <Link
                    key={proj.id}
                    href={`/projects/${proj.id}`}
                    className="block rounded-xl border border-border bg-card p-5 hover:border-primary/50 transition group"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2.5">
                          <span className="text-base font-bold text-main group-hover:text-primary-light transition">
                            {proj.name}
                          </span>
                          <span className="rounded bg-secondary px-2 py-0.5 font-mono text-[11px] text-muted border border-border">
                            {proj.language}
                          </span>
                        </div>
                        <p className="text-xs text-muted line-clamp-1">
                          {proj.description || `Source: ${proj.source_type}`}
                        </p>
                      </div>

                      <div className="flex items-center gap-4 text-xs font-mono shrink-0">
                        <div className="text-right">
                          <span className="text-error font-semibold">
                            {proj.detected_bugs_count || 0} issues
                          </span>
                          <p className="text-[11px] text-muted">{formatDate(proj.created_at)}</p>
                        </div>
                        <div className="rounded-full bg-secondary p-2 text-muted group-hover:text-primary-light transition">
                          <ArrowRight className="h-4 w-4" />
                        </div>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* ACTIVITY FEED (Col span 1) */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-main flex items-center gap-2">
                <Activity className="h-4 w-4 text-cyan" />
                Audit &amp; Activity Log
              </h2>
            </div>

            <div className="rounded-xl border border-border bg-card p-4 space-y-4 max-h-[500px] overflow-y-auto">
              {activities.length === 0 ? (
                <p className="text-xs text-muted text-center py-6">No recent events recorded.</p>
              ) : (
                activities.map((act) => (
                  <div key={act.id} className="flex gap-3 text-xs border-b border-border/40 pb-3 last:border-0 last:pb-0">
                    <span className="mt-1 h-2 w-2 rounded-full bg-primary-light shrink-0" />
                    <div className="space-y-1">
                      <p className="text-main leading-snug">{act.description}</p>
                      <span className="text-[10px] text-muted">{formatDate(act.created_at)}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

