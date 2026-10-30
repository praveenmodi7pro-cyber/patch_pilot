import "./globals.css"
import type { Metadata } from "next"
import Navbar from "@/components/Navbar"

export const metadata: Metadata = {
  title: "PatchPilot — Autonomous AI Software Debugging and Repair Platform",
  description: "Detect. Repair. Test. Verify. Autonomous AI debugging platform that verifies software fixes in isolated sandboxes.",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background text-main antialiased selection:bg-primary/30 selection:text-white">
        <Navbar />
        <main>{children}</main>
      </body>
    </html>
  )
}

