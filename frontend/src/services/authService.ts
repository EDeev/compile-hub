import { api, refreshAccessToken, setAccessToken, setSessionLostHandler } from "@/api/client"
import type { ApiUser, AuthResponse, UserSettings } from "@/api/types"
import { useUserStore } from "@/store/userStore"
import { useThemeStore } from "@/store/themeStore"
import { useEditorSettings } from "@/store/editorStore"
import { useLanguageStore } from "@/i18n"
import { useFileSystemStore } from "@/store/fileSystemStore"
import { useEditorState } from "@/store/editorStore"

/** Применить настройки аккаунта к интерфейсу (тема, язык, редактор). */
const applySettings = (settings: UserSettings) => {
  const theme = useThemeStore.getState()
  if (theme.theme !== settings.theme) theme.setTheme(settings.theme)
  useLanguageStore.getState().setLanguage(settings.uiLanguage)
  useEditorSettings.setState({ fontSize: settings.fontSize, autocomplete: settings.autocomplete })
}

const signIn = async ({ user, accessToken }: AuthResponse) => {
  setAccessToken(accessToken)
  useUserStore.getState().login(user)
  applySettings(user.settings)
  useEditorState.getState().closeFile()
  await useFileSystemStore.getState().afterLogin()
}

const signOut = () => {
  setAccessToken(null)
  useUserStore.getState().logout()
  useEditorState.getState().closeFile()
  useFileSystemStore.getState().afterLogout()
}

setSessionLostHandler(signOut)

export const AuthService = {
  /** При запуске: восстановить сессию по refresh-cookie. */
  async restore() {
    try {
      if (await refreshAccessToken()) {
        const user = await api<ApiUser>("/me")
        useUserStore.getState().login(user)
        applySettings(user.settings)
        await useFileSystemStore.getState().loadItems()
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
    const body = { username, email, password, uiLanguage }
    await signIn(await api<AuthResponse>("/auth/register", { method: "POST", body }))
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
  changePassword: (currentPassword: string, password: string) =>
    api("/auth/password/change", { method: "POST", body: { currentPassword, password } }),

  /** Сохранить настройку на сервере (у гостя — только локально). */
  async saveSettings(patch: Partial<UserSettings>) {
    if (useUserStore.getState().currentUser.isGuest) return
    await api<ApiUser>("/me/settings", { method: "PATCH", body: patch })
  }
}
