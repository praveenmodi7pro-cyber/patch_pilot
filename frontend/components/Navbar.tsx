"use client"

import React, { useEffect, useState } from "react"
import Link from "next/link"
import { ShieldCheck, Terminal, ArrowRight, UserCircle, LogOut } from "lucide-react"
import { api } from "@/services/api"
import { User } from "@/types"

export default function Navbar() {
  const [user, setUser] = useState<User | null>(null)

  useEffect(() => {
    const raw = localStorage.getItem("patchpilot_user")
    if (raw) {
      try {
        setUser(JSON.parse(raw))
      } catch {}
    }
  }, [])

  const handleLogout = async () => {
    await api.auth.logout()
    setUser(null)
    window.location.href = "/"
  }

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-border/80 bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-cyan text-white shadow-md shadow-primary/20">
            <Terminal className="h-5 w-5" />
          </div>
          <span className="text-xl font-bold tracking-tight text-main">
            Patch<span className="text-primary-light">Pilot</span>
          </span>
        </Link>

        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-muted">
          <Link href="#features" className="transition hover:text-main">
            Features
          </Link>
          <Link href="#how-it-works" className="transition hover:text-main">
            How It Works
          </Link>
          <Link href="#security" className="transition hover:text-main">
            Security
          </Link>
          <Link href="/dashboard" className="transition hover:text-main">
            Dashboard
          </Link>
        </div>

        <div className="flex items-center gap-4">
          {user ? (
            <div className="flex items-center gap-3">
              <Link
                href="/dashboard"
                className="flex items-center gap-2 rounded-lg bg-card px-3 py-1.5 text-sm font-medium text-main border border-border hover:border-muted/40 transition"
              >
                <UserCircle className="h-4 w-4 text-primary-light" />
                <span>{user.name.split(" ")[0]}</span>
              </Link>
              <button
                onClick={handleLogout}
                className="p-1.5 text-muted hover:text-error transition"
                title="Logout"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <Link
                href="/login"
                className="text-sm font-medium text-muted hover:text-main transition px-3 py-1.5"
              >
                Sign In
              </Link>
              <Link
                href="/register"
                className="flex items-center gap-1.5 rounded-lg bg-primary px-3.5 py-1.5 text-sm font-medium text-white shadow-sm hover:bg-primary-hover transition"
              >
                <span>Get Started</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  )
}

