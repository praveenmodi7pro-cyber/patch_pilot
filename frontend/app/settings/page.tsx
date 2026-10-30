"use client"

import React, { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Settings, UserCheck, Shield, Cpu, Key, CheckCircle2 } from "lucide-react"
import Sidebar from "@/components/Sidebar"
import { api } from "@/services/api"
import { User } from "@/types"

export default function SettingsPage() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    api.auth.getMe().then(setUser).catch(() => router.push("/login"))
  }, [router])

  return (
    <div className="flex min-h-[calc(100vh-4rem)] bg-background">
      <Sidebar />

      <main className="flex-1 p-6 sm:p-8 max-w-4xl space-y-8 overflow-y-auto">
        <div className="space-y-1 border-b border-border/60 pb-6">
          <h1 className="text-2xl sm:text-3xl font-extrabold text-main tracking-tight">
            Settings &amp; Platform Configuration
          </h1>
          <p className="text-sm text-muted">
            Manage your account credentials, AI provider settings, and sandbox safety controls.
          </p>
        </div>

        {saved && (
          <div className="flex items-center gap-2 rounded-lg border border-success/40 bg-success/10 p-4 text-sm text-success">
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            <span>Settings updated successfully.</span>
          </div>
        )}

        {/* ACCOUNT SETTINGS */}
        <div className="rounded-xl border border-border bg-card p-6 space-y-4">
          <h3 className="text-base font-bold text-main flex items-center gap-2">
            <UserCheck className="h-4 w-4 text-primary-light" />
            Developer Profile
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-muted uppercase">Full Name</label>
              <input
                type="text"
                disabled
                value={user?.name || ""}
                className="w-full rounded-lg border border-border bg-secondary px-3.5 py-2.5 text-sm text-main opacity-80"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-muted uppercase">Email Address</label>
              <input
                type="email"
                disabled
                value={user?.email || ""}
                className="w-full rounded-lg border border-border bg-secondary px-3.5 py-2.5 text-sm text-main opacity-80"
              />
            </div>
          </div>
        </div>

        {/* AI & SANDBOX TELEMETRY */}
        <div className="rounded-xl border border-border bg-card p-6 space-y-4">
          <h3 className="text-base font-bold text-main flex items-center gap-2">
            <Cpu className="h-4 w-4 text-cyan" />
            AI Reasoning Engine &amp; Sandbox Safety
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
            <div className="bg-secondary p-3.5 rounded border border-border space-y-1">
              <span className="text-muted block">AI Provider Engine</span>
              <span className="font-bold text-cyan text-sm block">Mock / Configured Provider</span>
              <span className="text-[10px] text-muted/70 block">Structured JSON Output Validation</span>
            </div>
            <div className="bg-secondary p-3.5 rounded border border-border space-y-1">
              <span className="text-muted block">Sandbox Mode</span>
              <span className="font-bold text-success text-sm block">Isolated Container / Restricted Subprocess</span>
              <span className="text-[10px] text-muted/70 block">Timeouts, CPU &amp; Memory Quotas</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

