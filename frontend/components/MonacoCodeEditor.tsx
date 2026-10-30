"use client"

import React from "react"
import dynamic from "next/dynamic"

// Dynamically import Monaco to prevent SSR window issues
const Editor = dynamic(() => import("@monaco-editor/react").then((mod) => mod.default), {
  ssr: false,
  loading: () => (
    <div className="flex h-full w-full items-center justify-center bg-card text-muted font-mono text-sm">
      Loading Code Editor...
    </div>
  ),
})

const DiffEditor = dynamic(() => import("@monaco-editor/react").then((mod) => mod.DiffEditor), {
  ssr: false,
  loading: () => (
    <div className="flex h-full w-full items-center justify-center bg-card text-muted font-mono text-sm">
      Loading Diff Viewer...
    </div>
  ),
})

interface MonacoCodeEditorProps {
  value: string
  language?: string
  readOnly?: boolean
  height?: string
  highlightLine?: number
  onChange?: (val: string | undefined) => void
}

export function MonacoCodeEditor({
  value,
  language = "python",
  readOnly = true,
  height = "100%",
  highlightLine,
  onChange,
}: MonacoCodeEditorProps) {
  return (
    <div className="h-full w-full overflow-hidden rounded-lg border border-border bg-[#0e1525]">
      <Editor
        height={height}
        language={language}
        value={value}
        theme="vs-dark"
        onChange={onChange}
        options={{
          readOnly,
          minimap: { enabled: false },
          fontSize: 13,
          lineNumbers: "on",
          scrollBeyondLastLine: false,
          automaticLayout: true,
          fontFamily: "'JetBrains Mono', 'Fira Code', 'Courier New', monospace",
          renderWhitespace: "selection",
        }}
      />
    </div>
  )
}

interface MonacoDiffViewerProps {
  original: string
  modified: string
  language?: string
  height?: string
}

export function MonacoDiffViewer({
  original,
  modified,
  language = "python",
  height = "550px",
}: MonacoDiffViewerProps) {
  return (
    <div className="h-full w-full overflow-hidden rounded-lg border border-border bg-[#0e1525]">
      <DiffEditor
        height={height}
        language={language}
        original={original}
        modified={modified}
        theme="vs-dark"
        options={{
          readOnly: true,
          minimap: { enabled: false },
          fontSize: 13,
          lineNumbers: "on",
          scrollBeyondLastLine: false,
          automaticLayout: true,
          fontFamily: "'JetBrains Mono', 'Fira Code', 'Courier New', monospace",
          renderSideBySide: true,
        }}
      />
    </div>
  )
}

