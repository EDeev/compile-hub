import { create } from "zustand"
import type { Language } from "@/api/types"
import { RunService } from "@/services/runService"

// запасной список, пока /api/languages не ответил (или недоступен)
const FALLBACK: Language[] = [
  {
    id: "python",
    name: "Python",
    extensions: ["py"],
    template: 'print("Hello, world!")\n',
    version: null,
    enabled: false
  },
  {
    id: "cpp",
    name: "C++",
    extensions: ["cpp", "cc", "cxx"],
    template: "",
    version: null,
    enabled: false
  },
  { id: "c", name: "C", extensions: ["c"], template: "", version: null, enabled: false },
  {
    id: "javascript",
    name: "JavaScript",
    extensions: ["js"],
    template: 'console.log("Hello, world!");\n',
    version: null,
    enabled: false
  },
  { id: "go", name: "Go", extensions: ["go"], template: "", version: null, enabled: false },
  { id: "java", name: "Java", extensions: ["java"], template: "", version: null, enabled: false }
]

interface LanguagesStore {
  languages: Language[]
  load: () => Promise<void>
}

export const useLanguagesStore = create<LanguagesStore>((set) => ({
  languages: FALLBACK,
  load: async () => {
    try {
      set({ languages: await RunService.languages() })
    } catch {
      // остаётся запасной список
    }
  }
}))

export const extensionOf = (name: string) => {
  const dot = name.lastIndexOf(".")
  return dot > 0 ? name.slice(dot + 1).toLowerCase() : ""
}

export const languageByName = (name: string): Language | undefined => {
  const ext = extensionOf(name)
  return useLanguagesStore.getState().languages.find((l) => l.extensions.includes(ext))
}
