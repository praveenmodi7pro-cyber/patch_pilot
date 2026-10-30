"use client"

import React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  LayoutDashboard,
  FolderGit2,
  PlusCircle,
  History,
  Settings,
  BookOpen,
  UserCheck,
  Terminal,
  LogOut,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { api } from "@/services/api"

export default function Sidebar() {
  const pathname = usePathname()

  const navItems = [
    { name: "Overview", href: "/dashboard", icon: LayoutDashboard },
    { name: "My Projects", href: "/dashboard#projects", icon: FolderGit2 },
    { name: "New Debugging Session", href: "/projects/new", icon: PlusCircle },
    { name: "Settings", href: "/settings", icon: Settings },
  ]

  const handleLogout = async () => {
    await api.auth.logout()
    window.location.href = "/login"
  }

  return (
    <aside className="w-64 border-r border-border bg-secondary/50 flex flex-col justify-between h-[calc(100vh-4rem)] sticky top-16 select-none">
      <div className="p-4 space-y-6">
        <div className="space-y-1">
          <p className="px-3 text-xs font-semibold text-muted uppercase tracking-wider mb-2">
            Debugging Console
          </p>
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.href
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition",
                  isActive
                    ? "bg-primary/15 text-primary-light font-semibold border border-primary/30"
                    : "text-muted hover:text-main hover:bg-card"
                )}
              >
                <Icon className={cn("h-4 w-4", isActive ? "text-primary-light" : "text-muted")} />
                {item.name}
              </Link>
            )
          })}
        </div>

        <div className="pt-4 border-t border-border/60 space-y-1">
          <p className="px-3 text-xs font-semibold text-muted uppercase tracking-wider mb-2">
            Documentation & Support
          </p>
          <a
            href="https://github.com"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-muted hover:text-main hover:bg-card transition"
          >
            <BookOpen className="h-4 w-4" />
            Documentation
          </a>
          <div className="flex items-center gap-3 px-3 py-2 text-xs text-muted/70">
            <span className="h-2 w-2 rounded-full bg-success" />
            Isolated Sandbox: Ready
          </div>
        </div>
      </div>

      <div className="p-4 border-t border-border bg-card/40">
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium text-muted hover:text-error hover:bg-error/10 transition"
        >
          <LogOut className="h-4 w-4" />
          Sign Out
        </button>
      </div>
    </aside>
  )
}

