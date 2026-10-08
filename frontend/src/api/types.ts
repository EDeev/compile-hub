// Типы ответов API (api/src/compilehub_api/schemas.py)

export interface UserSettings {
  theme: "dark" | "light"
  uiLanguage: "ru" | "en"
  fontSize: number
  autocomplete: boolean
}

export interface Limits {
  maxFiles: number | null
  maxFolders: number | null
  maxCodeBytes: number
  runsPerMinute: number | null
  runsPerDay: number | null
}

export interface Usage {
  files: number
  folders: number
  runsToday: number
}

export interface ApiUser {
  id: number
  username: string
  email: string
  emailVerified: boolean
  role: "user" | "admin"
  settings: UserSettings
  limits: Limits
  usage: Usage
  hasPassword: boolean
  oauth: string[]
}

export interface OAuthProvider {
  id: string
  name: string
}

export interface AuthResponse {
  user: ApiUser
  accessToken: string
}

export interface FileContent {
  id: number
  name: string
  type: "file"
  folder: number | null
  language: string
  size: string
  modified: string
  code: string
  stdin: string
}

export interface Language {
  id: string
  name: string
  extensions: string[]
  template: string
  version: string | null
  enabled: boolean
}

export type Verdict =
  | "OK"
  | "COMPILE_ERROR"
  | "RUNTIME_ERROR"
  | "TIME_LIMIT"
  | "MEMORY_LIMIT"
  | "OUTPUT_LIMIT"
  | "CANCELLED"
  | "INTERNAL_ERROR"

export interface RunCreated {
  runId: string
  streamToken: string
  position: number
}

export type RunEvent =
  | { type: "queued"; position: number }
  | { type: "compiling" }
  | { type: "running" }
  | { type: "stdout"; data: string }
  | { type: "stderr"; data: string }
  | { type: "compile_error"; output: string }
  | {
      type: "exit"
      verdict: Verdict
      exitCode?: number
      signal?: string
      timeMs?: number
      memoryKb?: number
    }
