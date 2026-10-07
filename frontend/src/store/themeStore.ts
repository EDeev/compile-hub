import { create } from "zustand"
import { persist } from "zustand/middleware"

type ThemeState = {
  theme: "light" | "dark"
  toggleTheme: () => void
  _applyThemeToDOM: (theme: "light" | "dark") => void
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: "dark",

      toggleTheme: () => {
        const newTheme = get().theme === "light" ? "dark" : "light"
        get()._applyThemeToDOM(newTheme)
        set({ theme: newTheme })
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
