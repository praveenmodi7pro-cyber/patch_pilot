"use client"

import React from "react"
import Link from "next/link"
import {
  ArrowRight,
  Shield,
  CheckCircle2,
  AlertCircle,
  FileCode2,
  Terminal,
  Cpu,
  Layers,
  Lock,
  GitBranch,
  Play,
  RotateCcw,
  Sparkles,
} from "lucide-react"

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen">
      {/* HERO SECTION */}
      <section className="relative overflow-hidden pt-20 pb-28 md:pt-28 md:pb-36 border-b border-border/60">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(99,102,241,0.15),rgba(255,255,255,0))]" />
        
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center max-w-3xl mx-auto space-y-6">
            <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3.5 py-1 text-xs font-semibold text-primary-light">
              <Sparkles className="h-3.5 w-3.5 text-cyan" />
              <span>Autonomous AI Software Debugging & Verification</span>
            </div>

            <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-main leading-[1.15]">
              Your AI Engineer That Doesn&apos;t Just Suggest.{" "}
              <span className="bg-gradient-to-r from-primary-light via-cyan to-primary bg-clip-text text-transparent">
                It Verifies.
              </span>
            </h1>

            <p className="text-lg sm:text-xl text-muted leading-relaxed max-w-2xl mx-auto">
              Upload your broken project. Let PatchPilot investigate the root cause, generate a repair, execute tests in an isolated sandbox, and verify whether your software works again.
            </p>

            <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
              <Link
                href="/projects/new"
                className="flex items-center gap-2 rounded-lg bg-primary px-6 py-3.5 text-sm font-semibold text-white shadow-lg shadow-primary/25 hover:bg-primary-hover transition"
              >
                <span>Start Debugging</span>
                <ArrowRight className="h-4 w-4" />
              </Link>
              <a
                href="#how-it-works"
                className="flex items-center gap-2 rounded-lg bg-card px-6 py-3.5 text-sm font-semibold text-main border border-border hover:border-muted/50 hover:bg-secondary transition"
              >
                <span>See How It Works</span>
              </a>
            </div>
          </div>

          {/* DEVELOPER HERO VISUAL */}
          <div className="mt-14 max-w-5xl mx-auto rounded-xl border border-border bg-card/90 shadow-2xl overflow-hidden backdrop-blur-xl">
            <div className="flex items-center justify-between border-b border-border/80 bg-secondary/80 px-4 py-3">
              <div className="flex items-center gap-2">
                <span className="h-3 w-3 rounded-full bg-error/80" />
                <span className="h-3 w-3 rounded-full bg-warning/80" />
                <span className="h-3 w-3 rounded-full bg-success/80" />
                <span className="ml-2 font-mono text-xs text-muted">patchpilot_workspace / app / calculator.py</span>
              </div>
              <div className="flex items-center gap-3 font-mono text-xs">
                <span className="flex items-center gap-1.5 text-success">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Tests Executed: 4/4 Passed
                </span>
                <span className="rounded bg-success/20 px-2 py-0.5 text-success font-bold">
                  VERIFIED
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-border">
              {/* Left side: Detected Bug */}
              <div className="p-5 font-mono text-xs space-y-3 bg-[#0d1321]">
                <div className="flex items-center justify-between text-muted border-b border-border/40 pb-2">
                  <span className="text-error font-semibold flex items-center gap-1.5">
                    <AlertCircle className="h-4 w-4" />
                    Detected Issue: ZeroDivisionError
                  </span>
                  <span>calculator.py:16</span>
                </div>
                <div className="space-y-1 text-muted/90 pt-1 leading-5">
                  <p className="text-muted/60"># Original Implementation</p>
                  <p className="text-main">def divide(a: float, b: float) -&gt; float:</p>
                  <p className="text-error bg-error/15 px-1 py-0.5 rounded border border-error/30">
                    - &nbsp;&nbsp;&nbsp;&nbsp;return a / b &nbsp;&nbsp;# Unhandled division by zero
                  </p>
                </div>
                <div className="mt-4 pt-3 border-t border-border/40">
                  <p className="text-xs text-muted uppercase font-semibold tracking-wider">Root Cause Analysis</p>
                  <p className="text-muted/80 text-[11px] mt-1 leading-relaxed">
                    Function lacks zero divisor validation. Invoking divide(10, 0) triggers unhandled ZeroDivisionError crashing client operations.
                  </p>
                </div>
              </div>

              {/* Right side: Generated Patch & Verification */}
              <div className="p-5 font-mono text-xs space-y-3 bg-[#0a101d]">
                <div className="flex items-center justify-between text-muted border-b border-border/40 pb-2">
                  <span className="text-success font-semibold flex items-center gap-1.5">
                    <CheckCircle2 className="h-4 w-4" />
                    Verified Patch (Unified Diff)
                  </span>
                  <span className="text-primary-light">Sandbox: Isolated</span>
                </div>
                <div className="space-y-1 text-muted/90 pt-1 leading-5">
                  <p className="text-muted/60"># Proposed Minimal Patch</p>
                  <p className="text-main">def divide(a: float, b: float) -&gt; float:</p>
                  <p className="text-success bg-success/15 px-1 py-0.5 rounded border border-success/30">
                    + &nbsp;&nbsp;&nbsp;&nbsp;if b == 0: raise ValueError(&apos;Cannot divide by zero&apos;)
                  </p>
                  <p className="text-main">&nbsp;&nbsp;&nbsp;&nbsp;return a / b</p>
                </div>
                <div className="mt-4 pt-3 border-t border-border/40 bg-card/40 p-2.5 rounded border border-border/60">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-muted">Pytest Runner Result:</span>
                    <span className="text-success font-bold">test_divide_by_zero PASSED (0.04s)</span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] mt-1">
                    <span className="text-muted">Regression Check:</span>
                    <span className="text-main">0 regressions detected</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 6-STEP HOW IT WORKS WORKFLOW */}
      <section id="how-it-works" className="py-24 border-b border-border/60 bg-secondary/30">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto space-y-3 mb-16">
            <h2 className="text-xs font-bold tracking-widest text-primary-light uppercase">
              Predictable Engineering
            </h2>
            <h3 className="text-3xl font-extrabold text-main">
              The 6-Step Autonomous Verification Workflow
            </h3>
            <p className="text-muted text-sm sm:text-base">
              A patch is never declared successful until it passes isolated automated execution.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              {
                step: "01",
                title: "Repository Ingestion",
                desc: "Safely extract repository archives, scrub sensitive secrets, scan AST structures, and index manifest dependencies.",
                icon: FileCode2,
              },
              {
                step: "02",
                title: "Bug & Vulnerability Detection",
                desc: "Correlate syntax anomalies, Ruff static diagnostics, and baseline test failures to isolate concrete issues.",
                icon: AlertCircle,
              },
              {
                step: "03",
                title: "Root Cause Investigation",
                desc: "Formulate rigorous, evidence-backed explanations of why bugs occur with confidence scoring.",
                icon: Cpu,
              },
              {
                step: "04",
                title: "Minimal Patch Formulation",
                desc: "Synthesize minimal unified git diffs that correct errors while strictly preserving existing architecture.",
                icon: GitBranch,
              },
              {
                step: "05",
                title: "Isolated Sandbox Execution",
                desc: "Apply the patch in an isolated working copy and execute test suites under strict resource and timeout limits.",
                icon: Play,
              },
              {
                step: "06",
                title: "Regression Verification & Report",
                desc: "Compare baseline vs patched outputs to verify zero regressions before rendering a transparent audit report.",
                icon: CheckCircle2,
              },
            ].map((item) => {
              const Icon = item.icon
              return (
                <div
                  key={item.step}
                  className="rounded-xl border border-border bg-card p-6 space-y-4 hover:border-primary/40 transition group"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary-light group-hover:bg-primary group-hover:text-white transition">
                      <Icon className="h-5 w-5" />
                    </div>
                    <span className="font-mono text-sm font-bold text-muted/60">{item.step}</span>
                  </div>
                  <h4 className="text-base font-bold text-main">{item.title}</h4>
                  <p className="text-sm text-muted leading-relaxed">{item.desc}</p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* CORE FEATURES */}
      <section id="features" className="py-24 border-b border-border/60">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto space-y-3 mb-16">
            <h2 className="text-xs font-bold tracking-widest text-cyan uppercase">
              Engineered for Accuracy
            </h2>
            <h3 className="text-3xl font-extrabold text-main">
              Built for Developers Who Demand Proof
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="rounded-xl border border-border bg-card p-8 space-y-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-cyan/15 text-cyan">
                <Shield className="h-5 w-5" />
              </div>
              <h4 className="text-xl font-bold text-main">Zero Blind Assumptions</h4>
              <p className="text-muted leading-relaxed text-sm">
                Unlike chat-based AI assistants that output untested code suggestions, PatchPilot enforces an explicit contract: a suggestion is not a fix until it compiles, applies cleanly, and passes automated verification tests.
              </p>
            </div>

            <div className="rounded-xl border border-border bg-card p-8 space-y-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/15 text-primary-light">
                <RotateCcw className="h-5 w-5" />
              </div>
              <h4 className="text-xl font-bold text-main">Automated Regression Detection</h4>
              <p className="text-muted leading-relaxed text-sm">
                Patches that resolve an existing bug but break other unit tests are automatically flagged and rejected. You receive full before-and-after test comparisons.
              </p>
            </div>

            <div className="rounded-xl border border-border bg-card p-8 space-y-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-warning/15 text-warning">
                <Layers className="h-5 w-5" />
              </div>
              <h4 className="text-xl font-bold text-main">Multi-Stage Modular Pipeline</h4>
              <p className="text-muted leading-relaxed text-sm">
                PatchPilot divides debugging into specialized steps: repository manifest parsing, static code analysis, AST parsing, root cause analysis, unified diff generation, and sandbox evaluation.
              </p>
            </div>

            <div className="rounded-xl border border-border bg-card p-8 space-y-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-success/15 text-success">
                <CheckCircle2 className="h-5 w-5" />
              </div>
              <h4 className="text-xl font-bold text-main">Downloadable Audit Reports</h4>
              <p className="text-muted leading-relaxed text-sm">
                Every repair session produces a structured 11-section verification audit that details root causes, unified diffs, test logs, remaining risks, and can be exported as a professional PDF.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* SECURITY SECTION */}
      <section id="security" className="py-24 border-b border-border/60 bg-secondary/20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mx-auto space-y-6 text-center">
            <div className="inline-flex items-center gap-2 rounded-full border border-success/30 bg-success/10 px-3.5 py-1 text-xs font-semibold text-success">
              <Lock className="h-3.5 w-3.5" />
              <span>Enterprise-Grade Security Architecture</span>
            </div>
            <h3 className="text-3xl font-extrabold text-main">
              Untrusted Code Never Compromises Your Infrastructure
            </h3>
            <p className="text-muted text-sm sm:text-base leading-relaxed">
              Uploaded repositories and test suites run in strictly isolated sandboxes with no network egress, restricted CPU/memory quotas, and non-root process privileges.
            </p>
          </div>

          <div className="mt-12 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                title: "Sandbox Isolation",
                desc: "Code execution occurs inside isolated sandboxes, entirely separated from backend web processes.",
              },
              {
                title: "Secret Scrubbing",
                desc: "Credentials, AWS keys, and private keys are scrubbed and redacted before AI prompt transmission.",
              },
              {
                title: "No Auto-Merge",
                desc: "Patches are never automatically pushed or merged to external GitHub repositories without explicit developer approval.",
              },
              {
                title: "Path Traversal Defense",
                desc: "Archive extractors enforce strict path boundary checks to prevent Zip Slip and directory escape attacks.",
              },
            ].map((s) => (
              <div key={s.title} className="rounded-xl border border-border bg-card p-5 space-y-2.5">
                <h5 className="text-sm font-bold text-main flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-cyan" />
                  {s.title}
                </h5>
                <p className="text-xs text-muted leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="py-12 bg-background">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-6 text-xs text-muted">
          <div className="flex items-center gap-2">
            <Terminal className="h-4 w-4 text-primary-light" />
            <span className="font-bold text-main">PatchPilot</span>
            <span>— Detect. Repair. Test. Verify.</span>
          </div>
          <div className="flex items-center gap-6">
            <Link href="#features" className="hover:text-main transition">Features</Link>
            <Link href="#how-it-works" className="hover:text-main transition">Workflow</Link>
            <Link href="#security" className="hover:text-main transition">Security</Link>
            <Link href="/login" className="hover:text-main transition">Sign In</Link>
            <Link href="/register" className="hover:text-main transition">Get Started</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}

