// HTTP-клиент API: относительный /api (тот же домен — без CORS), Bearer-токен в памяти,
// refresh-токен — httpOnly-cookie; при 401 token_expired токен обновляется один раз и запрос повторяется.

export class ApiError extends Error {
  status: number
  code: string
  details?: Record<string, unknown>

  constructor(status: number, code: string, message: string, details?: Record<string, unknown>) {
    super(message)
    this.status = status
    this.code = code
    this.details = details
  }
}

let accessToken: string | null = null
let refreshing: Promise<boolean> | null = null
let onSessionLost: (() => void) | null = null

export const setAccessToken = (token: string | null) => {
  accessToken = token
}

export const hasAccessToken = () => accessToken !== null

/** Вызывается, когда сессию восстановить нельзя (refresh отклонён) — например, чтобы выйти в гостя. */
export const setSessionLostHandler = (handler: () => void) => {
  onSessionLost = handler
}

/** Обновить access-токен по refresh-cookie; параллельные вызовы ждут один запрос. */
export const refreshAccessToken = (): Promise<boolean> => {
  refreshing ??= (async () => {
    try {
      const response = await fetch("/api/auth/refresh", {
        method: "POST",
        credentials: "same-origin"
      })
      if (!response.ok) return false
      accessToken = ((await response.json()) as { accessToken: string }).accessToken
      return true
    } catch {
      return false
    } finally {
      refreshing = null
    }
  })()
  return refreshing
}

interface RequestOptions {
  method?: string
  body?: unknown
  query?: Record<string, string | number | undefined>
}

const parseError = async (response: Response): Promise<ApiError> => {
  try {
    const { error } = (await response.json()) as {
      error: { code: string; message: string; details?: Record<string, unknown> }
    }
    return new ApiError(response.status, error.code, error.message, error.details)
  } catch {
    return new ApiError(response.status, "http_error", response.statusText || "Request failed")
  }
}

export async function api<T = void>(
  path: string,
  options: RequestOptions = {},
  retry = true
): Promise<T> {
  const url = new URL(`/api${path}`, window.location.origin)
  for (const [key, value] of Object.entries(options.query ?? {})) {
    if (value !== undefined) url.searchParams.set(key, String(value))
  }
  const headers: Record<string, string> = {}
  if (options.body !== undefined) headers["Content-Type"] = "application/json"
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`

  let response: Response
  try {
    response = await fetch(url, {
      method: options.method ?? "GET",
      headers,
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
      credentials: "same-origin"
    })
  } catch {
    throw new ApiError(0, "network_error", "Network error")
  }

  if (response.status === 401 && retry && accessToken) {
    const error = await parseError(response)
    if (error.code === "token_expired" || error.code === "unauthorized") {
      if (await refreshAccessToken()) return api<T>(path, options, false)
      accessToken = null
      onSessionLost?.()
    }
    throw error
  }
  if (!response.ok) throw await parseError(response)
  if (response.status === 204 || response.status === 202) {
    const text = await response.text()
    return (text ? JSON.parse(text) : undefined) as T
  }
  return (await response.json()) as T
}
