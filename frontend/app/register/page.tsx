"use client"

import React, { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Terminal, ArrowRight, AlertCircle, Loader2 } from "lucide-react"
import { api } from "@/services/api"

export default function RegisterPage() {
  const router = useRouter()
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (password.length < 8) {
      setError("Password must be at least 8 characters long.")
      return
    }

    setLoading(true)
    try {
      await api.auth.register(name, email, password)
      router.push("/dashboard")
    } catch (err: any) {
      setError(err.message || "Registration failed. Please check your inputs.")
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
          <h2 className="text-2xl font-bold tracking-tight text-main">Create your account</h2>
          <p className="text-sm text-muted">
            Start autonomous debugging and verified code repair
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
            <label className="text-xs font-semibold text-muted uppercase">Full Name</label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Alex Chen"
              className="w-full rounded-lg border border-border bg-secondary px-3.5 py-2.5 text-sm text-main placeholder-muted/60 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary transition"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted uppercase">Email address</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="alex@company.com"
              className="w-full rounded-lg border border-border bg-secondary px-3.5 py-2.5 text-sm text-main placeholder-muted/60 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary transition"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted uppercase">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              className="w-full rounded-lg border border-border bg-secondary px-3.5 py-2.5 text-sm text-main placeholder-muted/60 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary transition"
            />
            <p className="text-[11px] text-muted/70">Minimum 8 characters.</p>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 rounded-lg bg-primary py-2.5 text-sm font-semibold text-white shadow-md hover:bg-primary-hover focus:outline-none transition disabled:opacity-50"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Create Account"}
            {!loading && <ArrowRight className="h-4 w-4" />}
          </button>
        </form>

        <div className="pt-2 text-center text-xs text-muted">
          Already have an account?{" "}
          <Link href="/login" className="font-semibold text-primary-light hover:underline">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  )
}

