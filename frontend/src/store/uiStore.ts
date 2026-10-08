import { create } from "zustand"

export type EditorTab = "code" | "input" | "console"

interface UiStore {
  /** выдвижная панель файлов на телефоне */
  filesOpen: boolean
  setFilesOpen: (open: boolean) => void
  /** активная вкладка редактора на телефоне */
  editorTab: EditorTab
  setEditorTab: (tab: EditorTab) => void
}

export const useUiStore = create<UiStore>((set) => ({
  filesOpen: false,
  setFilesOpen: (filesOpen) => set({ filesOpen }),
  editorTab: "code",
  setEditorTab: (editorTab) => set({ editorTab })
}))
