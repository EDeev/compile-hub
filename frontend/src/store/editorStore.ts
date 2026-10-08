import type { FileItem } from "@/types"
import { create } from "zustand"
import { persist } from "zustand/middleware"
import { toast } from "react-toastify"
import type { RunEvent, Verdict } from "@/api/types"
import { RunService, type RunStream } from "@/services/runService"
import { useFileSystemStore } from "./fileSystemStore"
import { useUserStore } from "./userStore"
import { languageByName } from "./languagesStore"
import { errorMessage, t } from "@/i18n"

/** Консоль (xterm) регистрирует себя здесь — стор пишет в неё вывод запуска. */
export interface ConsoleSink {
  write: (text: string) => void
  clear: () => void
}

let sink: ConsoleSink | null = null
export const setConsoleSink = (value: ConsoleSink | null) => {
  sink = value
}

const RED = "\x1b[31m"
const DIM = "\x1b[2m"
const RESET = "\x1b[0m"
// xterm переводит строку только по \r\n
const crlf = (text: string) => text.replace(/\r?\n/g, "\r\n")

export type RunStatus = "idle" | "starting" | "queued" | "compiling" | "running" | "finished"

export interface RunResult {
  verdict: Verdict
  exitCode?: number
  signal?: string
  timeMs?: number
  memoryKb?: number
}

interface EditorState {
  currentFile: FileItem | null
  code: string
  stdin: string
  savedCode: string
  savedStdin: string
  isLoadingFile: boolean
  isSaving: boolean

  status: RunStatus
  position: number
  interactive: boolean
  result: RunResult | null

  openFile: (file: FileItem) => Promise<void>
  closeFile: () => void
  setCode: (code: string) => void
  setStdin: (stdin: string) => void
  save: () => Promise<void>
  run: () => Promise<void>
  stop: () => void
  sendInput: (data: string) => void
  endInput: () => void
}

let stream: RunStream | null = null

export const useEditorState = create<EditorState>((set, get) => {
  const onEvent = (event: RunEvent) => {
    switch (event.type) {
      case "queued":
        set({ status: "queued", position: event.position })
        break
      case "compiling":
        set({ status: "compiling" })
        break
      case "running":
        set({ status: "running" })
        break
      case "stdout":
        sink?.write(crlf(event.data))
        break
      case "stderr":
        sink?.write(RED + crlf(event.data) + RESET)
        break
      case "compile_error":
        sink?.write(RED + crlf(event.output) + RESET)
        break
      case "exit": {
        const { type: _, ...result } = event
        set({ status: "finished", result })
        const details = [
          t(`verdict.${event.verdict}`),
          event.exitCode !== undefined && event.exitCode !== null && event.exitCode !== 0
            ? t("editor.exitCode", { code: event.exitCode })
            : null,
          event.signal ? t("editor.signal", { signal: event.signal }) : null,
          event.timeMs !== undefined ? `${event.timeMs} ms` : null,
          event.memoryKb !== undefined ? `${(event.memoryKb / 1024).toFixed(1)} MB` : null
        ].filter(Boolean)
        sink?.write(`\r\n${DIM}— ${details.join(" · ")}${RESET}\r\n`)
        break
      }
    }
  }

  return {
    currentFile: null,
    code: "",
    stdin: "",
    savedCode: "",
    savedStdin: "",
    isLoadingFile: false,
    isSaving: false,
    status: "idle",
    position: 0,
    interactive: false,
    result: null,

    openFile: async (file) => {
      if (get().currentFile?.id === file.id) return
      get().stop()
      set({
        currentFile: file,
        isLoadingFile: true,
        code: "",
        stdin: "",
        result: null,
        status: "idle"
      })
      sink?.clear()
      const content = await useFileSystemStore.getState().getContent(file)
      if (get().currentFile?.id !== file.id) return // пока грузили, открыли другой файл
      set({
        isLoadingFile: false,
        code: content?.code ?? "",
        stdin: content?.stdin ?? "",
        savedCode: content?.code ?? "",
        savedStdin: content?.stdin ?? ""
      })
    },

    closeFile: () => {
      get().stop()
      set({
        currentFile: null,
        code: "",
        stdin: "",
        savedCode: "",
        savedStdin: "",
        result: null,
        status: "idle"
      })
    },

    setCode: (code) => set({ code }),
    setStdin: (stdin) => set({ stdin }),

    save: async () => {
      const { currentFile, code, stdin, isSaving } = get()
      if (!currentFile || isSaving) return
      set({ isSaving: true })
      const ok = await useFileSystemStore.getState().saveContent(currentFile, { code, stdin })
      set({ isSaving: false, ...(ok ? { savedCode: code, savedStdin: stdin } : {}) })
      if (ok) toast.success(t("editor.saved"), { autoClose: 1200 })
    },

    run: async () => {
      const { currentFile, code, stdin, status } = get()
      if (!currentFile || ["starting", "queued", "compiling", "running"].includes(status)) return
      const language = languageByName(currentFile.name)
      if (!language?.enabled) {
        toast.error(t("editor.languageDisabled", { language: language?.name ?? currentFile.name }))
        return
      }
      // пустое поле ввода — программа читает ввод из консоли по ходу выполнения
      const interactive = stdin.trim() === ""
      sink?.clear()
      set({ status: "starting", result: null, interactive })
      try {
        const created = await RunService.create({
          language: language.id,
          code,
          stdin,
          fileId: useUserStore.getState().currentUser.isGuest ? null : currentFile.id, // у гостя файлы локальные
          interactive
        })
        stream = RunService.stream(created, onEvent, (finished) => {
          stream = null
          if (!finished) set({ status: "idle" })
        })
      } catch (error) {
        set({ status: "idle" })
        toast.error(errorMessage(error))
      }
    },

    stop: () => {
      stream?.kill()
    },

    sendInput: (data) => stream?.sendInput(data),
    endInput: () => stream?.endInput()
  }
})

interface EditorSettings {
  fontSize: number
  autocomplete: boolean
  changeFontSize: (newSize: number) => void
  switchAutocomplete: () => void
}

// размер шрифта и подсказки — в localStorage; у вошедшего синхронизируются с сервером
export const useEditorSettings = create<EditorSettings>()(
  persist(
    (set, get) => ({
      fontSize: 14,
      autocomplete: true,
      changeFontSize: (newSize: number) => set({ fontSize: newSize }),
      switchAutocomplete: () => set({ autocomplete: !get().autocomplete })
    }),
    { name: "editor-settings" }
  )
)
