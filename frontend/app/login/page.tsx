"use client"

import React, { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Terminal, ArrowRight, AlertCircle, Loader2 } from "lucide-react"
import { api } from "@/services/api"

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      await api.auth.login(email, password)
      router.push("/dashboard")
    } catch (err: any) {
      setError(err.message || "Invalid credentials. Please verify your email and password.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center px-4 py-12">
      <div className="w-full max-w-md space-y-8 rounded-2xl border border-border bg-card p-8 shadow-2xl backdrop-blur-md">
        <div className="text-center space-y-2">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-cyan text-white shadow-lg shadow-primary/20">
            <Terminal className="h-6 w-6" />
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-main">Welcome back</h2>
          <p className="text-sm text-muted">
            Sign in to your PatchPilot autonomous debugging console
          </p>
        </div>

        {error && (
          <div className="flex items-center gap-2 rounded-lg border border-error/40 bg-error/10 p-3 text-sm text-error">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted uppercase">Email address</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="developer@company.com"
              className="w-full rounded-lg border border-border bg-secondary px-3.5 py-2.5 text-sm text-main placeholder-muted/60 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary transition"
            />
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-muted uppercase">Password</label>
              <Link href="/forgot-password" className="text-xs text-primary-light hover:underline">
                Forgot password?
              </Link>
            </div>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              className="w-full rounded-lg border border-border bg-secondary px-3.5 py-2.5 text-sm text-main placeholder-muted/60 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary transition"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 rounded-lg bg-primary py-2.5 text-sm font-semibold text-white shadow-md hover:bg-primary-hover focus:outline-none transition disabled:opacity-50"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Sign in to Dashboard"}
            {!loading && <ArrowRight className="h-4 w-4" />}
          </button>
        </form>

        <div className="pt-2 text-center text-xs text-muted">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="font-semibold text-primary-light hover:underline">
            Register for free
          </Link>
        </div>

        {/* Demo login shortcut */}
        <div className="pt-4 border-t border-border/60 text-center">
          <p className="text-xs text-muted/70 mb-2">Evaluation credentials:</p>
          <button
            type="button"
            onClick={() => {
              setEmail("demo@patchpilot.io")
              setPassword("PatchPilot123!")
            }}
            className="inline-block text-xs font-mono text-cyan hover:underline"
          >
            Use Demo Account (demo@patchpilot.io)
          </button>
        </div>
      </div>
    </div>
  )
}

