import { api, refreshAccessToken, setAccessToken, setSessionLostHandler } from "@/api/client"
import type { ApiUser, AuthResponse, OAuthProvider, UserSettings } from "@/api/types"
import { useUserStore } from "@/store/userStore"
import { useThemeStore } from "@/store/themeStore"
import { useEditorSettings } from "@/store/editorStore"
import { t, useLanguageStore, type MessageKey } from "@/i18n"
import { toast } from "react-toastify"
import { useFileSystemStore } from "@/store/fileSystemStore"
import { useEditorState } from "@/store/editorStore"

/** Применить настройки аккаунта к интерфейсу (тема, язык, редактор). */
const applySettings = (settings: UserSettings) => {
  const theme = useThemeStore.getState()
  if (theme.theme !== settings.theme) theme.setTheme(settings.theme)
  useLanguageStore.getState().setLanguage(settings.uiLanguage)
  useEditorSettings.setState({ fontSize: settings.fontSize, autocomplete: settings.autocomplete })
}

// признак «был вход»: гостю не нужен запрос refresh при открытии сайта (иначе 401 в консоли браузера)
const SESSION_FLAG = "ch_session"
const markSession = (on: boolean) => {
  try {
    if (on) localStorage.setItem(SESSION_FLAG, "1")
    else localStorage.removeItem(SESSION_FLAG)
  } catch {
    // localStorage недоступен — просто попробуем refresh в следующий раз
  }
}

const signIn = async ({ user, accessToken }: AuthResponse) => {
  markSession(true)
  setAccessToken(accessToken)
  useUserStore.getState().login(user)
  applySettings(user.settings)
  useEditorState.getState().closeFile()
  await useFileSystemStore.getState().afterLogin()
}

const signOut = () => {
  markSession(false)
  setAccessToken(null)
  useUserStore.getState().logout()
  useEditorState.getState().closeFile()
  useFileSystemStore.getState().afterLogout()
}

setSessionLostHandler(signOut)

/** Возврат с Яндекса/VK: /?oauth=ok|linked или /?oauth_error=код — разобрать и убрать из адреса. */
const takeOAuthResult = (): { result: string | null; error: string | null } => {
  const params = new URLSearchParams(window.location.search)
  const result = params.get("oauth")
  const error = params.get("oauth_error")
  if (result || error) {
    params.delete("oauth")
    params.delete("oauth_error")
    const query = params.toString()
    window.history.replaceState(null, "", window.location.pathname + (query ? `?${query}` : ""))
  }
  return { result, error }
}

export const AuthService = {
  /** При запуске: восстановить сессию по refresh-cookie (в том числе сразу после входа через сервис). */
  async restore() {
    const { result, error } = takeOAuthResult()
    if (result === "ok") markSession(true)
    if (error) toast.error(t(`oauth.error.${error}` as MessageKey) || t("error.default"))
    try {
      if (localStorage.getItem(SESSION_FLAG) && (await refreshAccessToken())) {
        const user = await api<ApiUser>("/me")
        useUserStore.getState().login(user)
        applySettings(user.settings)
        if (result === "ok") {
          toast.success(t("auth.loggedIn"))
          await useFileSystemStore.getState().afterLogin() // гостевые файлы — в аккаунт
        } else {
          await useFileSystemStore.getState().loadItems()
        }
        if (result === "linked") toast.success(t("oauth.linked"))
      }
    } catch {
      signOut()
    } finally {
      useUserStore.getState().setRestoring(false)
    }
  },

  async checkUsername(username: string): Promise<boolean> {
    return (await api<{ available: boolean }>("/auth/check-username", { query: { username } }))
      .available
  },

  async login(login: string, password: string) {
    await signIn(
      await api<AuthResponse>("/auth/login", { method: "POST", body: { login, password } })
    )
  },

  async register(username: string, email: string, password: string) {
    const uiLanguage = useLanguageStore.getState().language
    const theme = useThemeStore.getState().theme
    const body = { username, email, password, uiLanguage }
    const response = await api<AuthResponse>("/auth/register", { method: "POST", body })
    // выбранная до регистрации тема остаётся и сохраняется в аккаунте
    if (response.user.settings.theme !== theme) {
      response.user.settings.theme = theme
      setAccessToken(response.accessToken)
      await api("/me/settings", { method: "PATCH", body: { theme } }).catch(() => {})
    }
    await signIn(response)
  },

  async logout() {
    try {
      await api("/auth/logout", { method: "POST" })
    } finally {
      signOut()
    }
  },

  async refreshMe() {
    const user = await api<ApiUser>("/me")
    useUserStore.getState().login(user)
    return user
  },

  async verify(token: string) {
    const user = await api<ApiUser>("/auth/verify", { method: "POST", body: { token } })
    if (!useUserStore.getState().currentUser.isGuest) useUserStore.getState().login(user)
  },

  resendVerification: () => api("/auth/verify/resend", { method: "POST" }),
  forgotPassword: (email: string) =>
    api("/auth/password/forgot", { method: "POST", body: { email } }),
  resetPassword: (token: string, password: string) =>
    api("/auth/password/reset", { method: "POST", body: { token, password } }),
  async changePassword(currentPassword: string, password: string) {
    await api("/auth/password/change", { method: "POST", body: { currentPassword, password } })
    await AuthService.refreshMe()
  },

  oauthProviders: () => api<OAuthProvider[]>("/auth/oauth/providers"),

  /** Уйти на страницу входа сервиса; mode=link — привязать к текущему аккаунту. */
  async oauthStart(provider: string, mode: "login" | "link" = "login") {
    const { url } = await api<{ url: string }>(`/auth/oauth/${provider}/start`, {
      method: "POST",
      body: { mode }
    })
    window.location.assign(url)
  },

  async oauthUnlink(provider: string) {
    useUserStore
      .getState()
      .login(await api<ApiUser>(`/auth/oauth/${provider}`, { method: "DELETE" }))
  },

  /** Сохранить настройку на сервере (у гостя — только локально). */
  async saveSettings(patch: Partial<UserSettings>) {
    if (useUserStore.getState().currentUser.isGuest) return
    await api<ApiUser>("/me/settings", { method: "PATCH", body: patch })
  }
}
