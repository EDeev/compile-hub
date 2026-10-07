import type { FileItem } from "@/types"
import { create } from "zustand"
import { persist } from "zustand/middleware"

interface editorState {
  currentFile: FileItem | null
  code: string
  output: string
  isModified: boolean
  isCompiling: boolean
  awaitsInput: boolean
  // add autocomplete and fontSize

  setFile: (file: FileItem) => void // may be FileItem instead of fileId
  // switchLanguage: (newLang: string) => void
  setCode: (changedCode: string) => void
  compileCode: () => void
}

interface editorSettings {
  fontSize: number
  autocomplete: boolean
  changeFontSize: (newSize: number) => void
  switchAutocomplete: () => void
}

export const useEditorState = create<editorState>((set) => ({
  currentFile: null, // there should be the last file user worked with
  code: "",
  output: "",
  isModified: false,
  isCompiling: false,
  awaitsInput: false,
  setFile: (file: FileItem) => {
    // file must be setted by clicking on file card in filebar
    // then we have to load file content and display it in editor (setCode)
    // don't forget to save file content locally if it changes by user (for faster downloading)
    set({ currentFile: file })
  },
  setCode: (changedCode) => {
    set({ code: changedCode })
  },
  compileCode: () => {
    // code server-compiling here
    set({ isCompiling: true, output: "" })

    // stub below
    setTimeout(() => {
      set({ isCompiling: false })
      set({ output: "compiled code here" })
    }, 1500)
  }
}))

// we store fontSize and autocomplete in localStorage
export const useEditorSettings = create<editorSettings>()(
  persist(
    (set, get) => ({
      fontSize: 14,
      autocomplete: true,

      changeFontSize: (newSize: number) => {
        set({ fontSize: newSize })
      },

      switchAutocomplete: () => {
        const currentState = get().autocomplete
        set({ autocomplete: !currentState })
      }
    }),
    {
      name: "editor-settings"
    }
  )
)
