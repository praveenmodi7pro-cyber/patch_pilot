import {
  AuthResponse,
  User,
  Project,
  FileTreeNode,
  FileContent,
  Analysis,
  AnalysisStatus,
  Bug,
  Repair,
  RepairDiff,
  TestExecution,
  VerificationReport,
  DashboardStats,
  ActivityLog,
} from "@/types"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1"

function getAuthHeaders(): HeadersInit {
  const token = typeof window !== "undefined" ? localStorage.getItem("patchpilot_token") : null
  const headers: HeadersInit = {
    Accept: "application/json",
  }
  if (token) {
    headers["Authorization"] = `Bearer ${token}`
  }
  return headers
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${path}`
  const headers = {
    ...getAuthHeaders(),
    ...(options.headers || {}),
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: "include", // send cookies
  })

  if (!response.ok) {
    let errorDetail = "Request failed"
    try {
      const errJson = await response.json()
      errorDetail = errJson.detail || errJson.message || errorDetail
    } catch {
      // fallback
    }
    throw new Error(errorDetail)
  }

  if (response.status === 204) {
    return {} as T
  }

  return response.json()
}

export const api = {
  // Auth
  auth: {
    async register(name: string, email: string, password: string):Promise<AuthResponse> {
      const data = await request<AuthResponse>("/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password }),
      })
      if (typeof window !== "undefined") {
        localStorage.setItem("patchpilot_token", data.access_token)
        localStorage.setItem("patchpilot_user", JSON.stringify(data.user))
      }
      return data
    },

    async login(email: string, password: string): Promise<AuthResponse> {
      const data = await request<AuthResponse>("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      })
      if (typeof window !== "undefined") {
        localStorage.setItem("patchpilot_token", data.access_token)
        localStorage.setItem("patchpilot_user", JSON.stringify(data.user))
      }
      return data
    },

    async getMe(): Promise<User> {
      return request<User>("/auth/me")
    },

    async logout(): Promise<void> {
      try {
        await request("/auth/logout", { method: "POST" })
      } finally {
        if (typeof window !== "undefined") {
          localStorage.removeItem("patchpilot_token")
          localStorage.removeItem("patchpilot_user")
        }
      }
    },
  },

  // Projects
  projects: {
    async list(): Promise<Project[]> {
      return request<Project[]>("/projects")
    },

    async get(id: string): Promise<Project> {
      return request<Project>(`/projects/${id}`)
    },

    async uploadZip(file: File, name?: string, description?: string): Promise<Project> {
      const formData = new FormData()
      formData.append("file", file)
      if (name) formData.append("name", name)
      if (description) formData.append("description", description)

      const token = typeof window !== "undefined" ? localStorage.getItem("patchpilot_token") : null
      const headers: HeadersInit = {}
      if (token) headers["Authorization"] = `Bearer ${token}`

      const response = await fetch(`${API_BASE_URL}/projects/upload`, {
        method: "POST",
        headers,
        body: formData,
        credentials: "include",
      })

      if (!response.ok) {
        let err = "Upload failed"
        try {
          const j = await response.json()
          err = j.detail || err
        } catch {}
        throw new Error(err)
      }

      return response.json()
    },

    async loadSample(): Promise<Project> {
      return request<Project>("/projects/sample", { method: "POST" })
    },

    async importGitHub(url: string, branch = "main", name?: string): Promise<Project> {
      return request<Project>("/projects/github/import", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repository_url: url, branch, name }),
      })
    },

    async getFiles(projectId: string): Promise<FileTreeNode[]> {
      return request<FileTreeNode[]>(`/projects/${projectId}/files`)
    },

    async getFileContent(projectId: string, path: string): Promise<FileContent> {
      return request<FileContent>(`/projects/${projectId}/file?path=${encodeURIComponent(path)}`)
    },

    async delete(projectId: string): Promise<void> {
      return request<void>(`/projects/${projectId}`, { method: "DELETE" })
    },
  },

  // Analysis
  analysis: {
    async start(projectId: string): Promise<Analysis> {
      return request<Analysis>(`/projects/${projectId}/analyze`, { method: "POST" })
    },

    async get(analysisId: string): Promise<Analysis> {
      return request<Analysis>(`/analysis/${analysisId}`)
    },

    async getStatus(analysisId: string): Promise<AnalysisStatus> {
      return request<AnalysisStatus>(`/analysis/${analysisId}/status`)
    },

    async getBugs(analysisId: string): Promise<Bug[]> {
      return request<Bug[]>(`/analysis/${analysisId}/bugs`)
    },

    async cancel(analysisId: string): Promise<{ message: string }> {
      return request<{ message: string }>(`/analysis/${analysisId}/cancel`, { method: "POST" })
    },

    getEventSource(analysisId: string): EventSource {
      return new EventSource(`${API_BASE_URL}/analysis/${analysisId}/events`)
    },
  },

  // Bugs
  bugs: {
    async get(bugId: string): Promise<Bug> {
      return request<Bug>(`/bugs/${bugId}`)
    },

    async updateStatus(bugId: string, status: string): Promise<Bug> {
      return request<Bug>(`/bugs/${bugId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      })
    },

    async generateRepair(bugId: string): Promise<Repair> {
      return request<Repair>(`/bugs/${bugId}/generate-repair`, { method: "POST" })
    },
  },

  // Repairs
  repairs: {
    async get(repairId: string): Promise<Repair> {
      return request<Repair>(`/repairs/${repairId}`)
    },

    async getDiff(repairId: string): Promise<RepairDiff> {
      return request<RepairDiff>(`/repairs/${repairId}/diff`)
    },

    async approve(repairId: string): Promise<Repair> {
      return request<Repair>(`/repairs/${repairId}/approve`, { method: "POST" })
    },

    async reject(repairId: string): Promise<Repair> {
      return request<Repair>(`/repairs/${repairId}/reject`, { method: "POST" })
    },

    async apply(repairId: string): Promise<Repair> {
      return request<Repair>(`/repairs/${repairId}/apply`, { method: "POST" })
    },

    async regenerate(repairId: string): Promise<Repair> {
      return request<Repair>(`/repairs/${repairId}/regenerate`, { method: "POST" })
    },

    getDownloadUrl(repairId: string): string {
      return `${API_BASE_URL}/repairs/${repairId}/download`
    },
  },

  // Testing
  testing: {
    async runTests(repairId: string): Promise<TestExecution> {
      return request<TestExecution>(`/repairs/${repairId}/test`, { method: "POST" })
    },

    async listTests(repairId: string): Promise<TestExecution[]> {
      return request<TestExecution[]>(`/repairs/${repairId}/tests`)
    },

    async getTest(testExecutionId: string): Promise<TestExecution> {
      return request<TestExecution>(`/tests/${testExecutionId}`)
    },
  },

  // Reports
  reports: {
    async getReport(repairId: string): Promise<VerificationReport> {
      return request<VerificationReport>(`/repairs/${repairId}/report`)
    },

    getPdfUrl(repairId: string): string {
      return `${API_BASE_URL}/repairs/${repairId}/report/pdf`
    },
  },

  // Stats & Activity
  stats: {
    async getDashboardStats(): Promise<DashboardStats> {
      return request<DashboardStats>("/stats/dashboard")
    },

    async getActivity(): Promise<ActivityLog[]> {
      return request<ActivityLog[]>("/stats/activity")
    },
  },

  // GitHub
  github: {
    async getConnectUrl(): Promise<{ configured: boolean; message?: string; auth_url?: string }> {
      return request<{ configured: boolean; message?: string; auth_url?: string }>("/github/connect")
    },

    async listRepositories(): Promise<any[]> {
      return request<any[]>("/github/repositories")
    },
  },
}

