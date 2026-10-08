import { create } from "zustand"
import { persist } from "zustand/middleware"

type Theme = "light" | "dark"

type ThemeState = {
  theme: Theme
  toggleTheme: () => void
  setTheme: (theme: Theme) => void
  _applyThemeToDOM: (theme: Theme) => void
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: "dark",

      toggleTheme: () => get().setTheme(get().theme === "light" ? "dark" : "light"),

      setTheme: (theme) => {
        get()._applyThemeToDOM(theme)
        set({ theme })
      },

      _applyThemeToDOM: (theme) => {
        if (typeof document !== "undefined") {
          document.documentElement.setAttribute("data-theme", theme)
        }
      }
    }),
    {
      name: "theme-storage",
      onRehydrateStorage: () => (state) => {
        if (state) {
          state._applyThemeToDOM(state.theme)
        }
      }
    }
  )
)
