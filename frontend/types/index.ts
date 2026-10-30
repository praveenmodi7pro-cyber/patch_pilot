export interface User {
  id: string
  name: string
  email: string
  created_at: string
  updated_at: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export interface Project {
  id: string
  user_id: string
  name: string
  description?: string
  source_type: "zip" | "github"
  repository_url?: string
  repository_branch?: string
  commit_sha?: string
  language: string
  status: string
  created_at: string
  updated_at: string
  detected_bugs_count?: number
  generated_patches_count?: number
  last_analysis_status?: string
}

export interface FileTreeNode {
  name: string
  path: string
  is_directory: boolean
  children?: FileTreeNode[]
  size?: number
  language?: string
}

export interface FileContent {
  path: string
  language: string
  content: string
  size: number
}

export interface Bug {
  id: string
  analysis_id: string
  title: string
  category: "syntax_error" | "runtime_error" | "logic_error" | "static_check"
  severity: "critical" | "high" | "medium" | "low" | "informational"
  file_path: string
  line_number?: number
  description: string
  root_cause?: string
  evidence: string[]
  confidence: number
  status: "detected" | "reviewed" | "repairing" | "repaired" | "dismissed"
  created_at: string
}

export interface Repair {
  id: string
  bug_id: string
  analysis_id: string
  status: "generated" | "approved" | "rejected" | "applied" | "verified" | "failed"
  original_commit?: string
  patch_content: string
  files_changed: string[]
  explanation?: string
  approved_at?: string
  applied_at?: string
  created_at: string
  bug_title?: string
}

export interface RepairDiff {
  repair_id: string
  patch_content: string
  files: Array<{
    path: string
    original_code: string
    modified_code: string
    patch: string
  }>
  explanation?: string
}

export interface TestExecution {
  id: string
  repair_id: string
  status: "passed" | "failed" | "partially_passed" | "timed_out" | "error" | "no_tests_found"
  total_tests: number
  passed_tests: number
  failed_tests: number
  skipped_tests: number
  execution_duration: number
  stdout?: string
  stderr?: string
  started_at: string
  completed_at?: string
}

export interface VerificationReport {
  id: string
  repair_id: string
  status: "VERIFIED" | "PARTIALLY_VERIFIED" | "FAILED" | "INCONCLUSIVE"
  checks_performed: string[]
  checks_passed: string[]
  checks_failed: string[]
  remaining_risks: string[]
  report_content: {
    section_1_original_issue?: {
      title: string
      category: string
      severity: string
      file_path: string
      line_number?: number
      description: string
    }
    section_2_root_cause?: {
      root_cause: string
      evidence: string[]
      confidence: number
    }
    section_3_files_affected?: {
      files: string[]
      count: number
    }
    section_4_generated_patch?: {
      patch_content: string
      explanation: string
    }
    section_5_changes_applied?: {
      applied_at: string
      isolation_mode: string
      clean_application: boolean
    }
    section_6_tests_executed?: {
      runner: string
      total_tests: number
      duration_seconds: number
    }
    section_7_test_results?: {
      status: string
      passed: number
      failed: number
      skipped: number
      failures: any[]
    }
    section_8_regression_checks?: {
      has_regression: boolean
      fixed_tests: string[]
      new_regressions: string[]
      is_improved: boolean
    }
    section_9_verification_decision?: {
      final_verdict: string
      checks_passed: string[]
      checks_failed: string[]
    }
    section_10_remaining_risks?: {
      risks: string[]
    }
    section_11_recommended_next_action?: {
      recommendation: string
      can_auto_merge: boolean
      note: string
    }
  }
  created_at: string
}

export interface Analysis {
  id: string
  project_id: string
  status: string
  current_stage: string
  progress_metadata?: Record<string, any>
  error_message?: string
  started_at?: string
  completed_at?: string
  created_at: string
  bugs: Bug[]
}

export interface AnalysisStatus {
  id: string
  project_id: string
  status: string
  current_stage: string
  progress_percentage: number
  stages_completed: string[]
  error_message?: string
}

export interface DashboardStats {
  total_projects: number
  total_debugging_sessions: number
  bugs_detected: number
  repairs_verified: number
  repairs_awaiting_review: number
}

export interface ActivityLog {
  id: string
  user_id: string
  project_id?: string
  event_type: string
  description: string
  event_metadata?: Record<string, any>
  created_at: string
}

