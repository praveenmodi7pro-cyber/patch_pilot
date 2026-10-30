"use client"

import React, { useState } from "react"
import Link from "next/link"
import { Terminal, ArrowLeft, Mail, CheckCircle2 } from "lucide-react"

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("")
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitted(true)
  }

  return (
    <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center px-4 py-12">
      <div className="w-full max-w-md space-y-6 rounded-2xl border border-border bg-card p-8 shadow-2xl backdrop-blur-md">
        <div className="text-center space-y-2">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-card border border-border text-primary-light">
            <Mail className="h-6 w-6" />
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-main">Reset password</h2>
          <p className="text-sm text-muted">
            Enter your email to receive recovery instructions
          </p>
        </div>

        {submitted ? (
          <div className="rounded-xl border border-success/40 bg-success/10 p-4 text-center space-y-2">
            <CheckCircle2 className="mx-auto h-8 w-8 text-success" />
            <p className="text-sm font-semibold text-main">Reset Instructions Sent</p>
            <p className="text-xs text-muted">
              If an account is associated with {email}, you will receive a secure password reset link.
            </p>
            <div className="pt-3">
              <Link
                href="/login"
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-primary-light hover:underline"
              >
                <ArrowLeft className="h-3 w-3" />
                Return to Login
              </Link>
            </div>
          </div>
        ) : (
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

            <button
              type="submit"
              className="w-full rounded-lg bg-primary py-2.5 text-sm font-semibold text-white shadow-md hover:bg-primary-hover focus:outline-none transition"
            >
              Send Reset Instructions
            </button>

            <div className="text-center pt-2">
              <Link
                href="/login"
                className="inline-flex items-center gap-1.5 text-xs text-muted hover:text-main transition"
              >
                <ArrowLeft className="h-3 w-3" />
                Back to Sign in
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}

