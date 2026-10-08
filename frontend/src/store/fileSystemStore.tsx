import { create } from "zustand"
import { toast } from "react-toastify"
import { type FileItem, type FolderItem, type Item } from "@/types/fileSystem"
import { FileService } from "@/services/fileService"
import { useUserStore } from "./userStore"
import { useLanguagesStore, languageByName } from "./languagesStore"
import { GUEST_LIMITS } from "@/utils/constants"
import { useModalStore } from "@/store/modalStore"
import { ErrorModal } from "@/components/modals/ErrorModal"
import { errorMessage, t } from "@/i18n"

/*
  У вошедшего пользователя файлы живут на сервере, у гостя — в localStorage (до 10 файлов и 3 папок).
  После входа гостевые файлы переносятся в аккаунт (POST /files/import).
  tsx — чтобы передавать компоненты в openModal.
*/

const GUEST_ITEMS = "guest_files"
const GUEST_CODE = "guest_code"

interface Content {
  code: string
  stdin: string
}

const readJson = <T,>(key: string, fallback: T): T => {
  try {
    const raw = localStorage.getItem(key)
    return raw ? (JSON.parse(raw) as T) : fallback
  } catch {
    return fallback
  }
}

const guest = {
  items: () => readJson<Item[]>(GUEST_ITEMS, []),
  saveItems: (items: Item[]) =>
    localStorage.setItem(GUEST_ITEMS, JSON.stringify(items)),
  code: () => readJson<Record<number, Content>>(GUEST_CODE, {}),
  saveCode: (code: Record<number, Content>) =>
    localStorage.setItem(GUEST_CODE, JSON.stringify(code)),
  clear: () => {
    localStorage.removeItem(GUEST_ITEMS)
    localStorage.removeItem(GUEST_CODE)
  }
}

const humanSize = (n: number) =>
  n < 1024 ? `${n}b` : `${(n / 1024).toFixed(1).replace(/\.0$/, "")}kb`

const isGuest = () => useUserStore.getState().currentUser.isGuest

const fail = (error: unknown) => {
  toast.error(errorMessage(error))
  return null
}

interface FileSystemStore {
  items: Item[]
  isLoading: boolean

  loadItems: () => Promise<void>
  afterLogin: () => Promise<void>
  afterLogout: () => void

  createFile: (
    name: string,
    folderId: number | null
  ) => Promise<FileItem | null>
  createFolder: (name: string) => Promise<FolderItem | null>
  rename: (item: Item, name: string) => Promise<boolean>
  move: (item: FileItem, folderId: number | null) => Promise<boolean>
  remove: (item: Item) => Promise<boolean>

  getContent: (file: FileItem) => Promise<Content | null>
  saveContent: (file: FileItem, content: Content) => Promise<boolean>
}

export const useFileSystemStore = create<FileSystemStore>((set, get) => {
  const replace = (updated: Item) =>
    set((s) => ({
      items: s.items.map((i) =>
        i.id === updated.id && i.type === updated.type ? updated : i
      )
    }))

  const setGuestItems = (items: Item[]) => {
    guest.saveItems(items)
    set({ items })
  }

  const nextGuestId = () => Math.max(0, ...get().items.map((i) => i.id)) + 1

  const guestLimitReached = (type: "file" | "folder") => {
    const count = get().items.filter((i) => i.type === type).length
    if (
      count <
      (type === "file" ? GUEST_LIMITS.MAX_FILES : GUEST_LIMITS.MAX_FOLDERS)
    )
      return false
    useModalStore.getState().openModal(
      <ErrorModal
        title={t("files.guestLimitTitle")}
        message={t("files.guestLimit", {
          files: GUEST_LIMITS.MAX_FILES,
          folders: GUEST_LIMITS.MAX_FOLDERS
        })}
      />
    )
    return true
  }

  return {
    items: guest.items(),
    isLoading: false,

    loadItems: async () => {
      if (isGuest()) {
        set({ items: guest.items() })
        return
      }
      set({ isLoading: true })
      try {
        set({ items: await FileService.list() })
      } catch (error) {
        fail(error)
      } finally {
        set({ isLoading: false })
      }
    },

    afterLogin: async () => {
      const items = guest.items()
      if (items.length > 0) {
        const code = guest.code()
        try {
          const result = await FileService.importGuest({
            folders: items
              .filter((i) => i.type === "folder")
              .map((f) => ({ id: f.id, name: f.name })),
            files: items
              .filter((i): i is FileItem => i.type === "file")
              .map((f) => ({
                name: f.name,
                folder: f.folder,
                code: code[f.id]?.code ?? "",
                stdin: code[f.id]?.stdin ?? ""
              }))
          })
          guest.clear()
          const created = result.items.filter((i) => i.type === "file").length
          if (created) toast.success(t("auth.importDone", { count: created }))
          if (result.skipped)
            toast.warn(t("auth.importSkipped", { count: result.skipped }))
        } catch (error) {
          fail(error)
        }
      }
      await get().loadItems()
    },

    afterLogout: () => set({ items: guest.items() }),

    createFile: async (name, folderId) => {
      const template = languageByName(name)?.template ?? ""
      if (isGuest()) {
        if (guestLimitReached("file")) return null
        const file: FileItem = {
          id: nextGuestId(),
          name,
          type: "file",
          folder: folderId,
          language: languageByName(name)?.id,
          size: humanSize(new Blob([template]).size),
          modified: new Date().toISOString()
        }
        guest.saveCode({
          ...guest.code(),
          [file.id]: { code: template, stdin: "" }
        })
        setGuestItems([...get().items, file])
        return file
      }
      try {
        const file = await FileService.createFile(name, folderId)
        set((s) => ({ items: [...s.items, file] }))
        return file
      } catch (error) {
        return fail(error)
      }
    },

    createFolder: async (name) => {
      if (isGuest()) {
        if (guestLimitReached("folder")) return null
        const folder: FolderItem = {
          id: nextGuestId(),
          name,
          type: "folder",
          size: "0b",
          modified: new Date().toISOString()
        }
        setGuestItems([...get().items, folder])
        return folder
      }
      try {
        const folder = await FileService.createFolder(name)
        set((s) => ({ items: [folder, ...s.items] }))
        return folder
      } catch (error) {
        return fail(error)
      }
    },

    rename: async (item, name) => {
      if (isGuest()) {
        const language =
          item.type === "file" ? languageByName(name)?.id : undefined
        setGuestItems(
          get().items.map((i) =>
            i.id === item.id
              ? ({ ...i, name, ...(language ? { language } : {}) } as Item)
              : i
          )
        )
        return true
      }
      try {
        replace(
          item.type === "file"
            ? await FileService.patchFile(item.id, { name })
            : await FileService.renameFolder(item.id, name)
        )
        return true
      } catch (error) {
        return fail(error) ?? false
      }
    },

    move: async (item, folderId) => {
      if (isGuest()) {
        setGuestItems(
          get().items.map((i) =>
            i.id === item.id && i.type === "file"
              ? { ...i, folder: folderId }
              : i
          )
        )
        return true
      }
      try {
        replace(await FileService.patchFile(item.id, { folderId }))
        return true
      } catch (error) {
        return fail(error) ?? false
      }
    },

    remove: async (item) => {
      if (isGuest()) {
        const removed = new Set(
          get()
            .items.filter(
              (i) =>
                i.id === item.id ||
                (item.type === "folder" &&
                  i.type === "file" &&
                  i.folder === item.id)
            )
            .map((i) => i.id)
        )
        const code = guest.code()
        removed.forEach((id) => delete code[id])
        guest.saveCode(code)
        setGuestItems(get().items.filter((i) => !removed.has(i.id)))
        return true
      }
      try {
        await (item.type === "file"
          ? FileService.deleteFile(item.id)
          : FileService.deleteFolder(item.id))
        set((s) => ({
          items: s.items.filter(
            (i) =>
              i.id !== item.id &&
              !(
                item.type === "folder" &&
                i.type === "file" &&
                i.folder === item.id
              )
          )
        }))
        return true
      } catch (error) {
        return fail(error) ?? false
      }
    },

    getContent: async (file) => {
      if (isGuest()) return guest.code()[file.id] ?? { code: "", stdin: "" }
      try {
        const { code, stdin } = await FileService.get(file.id)
        return { code, stdin }
      } catch (error) {
        return fail(error)
      }
    },

    saveContent: async (file, content) => {
      if (isGuest()) {
        guest.saveCode({ ...guest.code(), [file.id]: content })
        const size = humanSize(new Blob([content.code]).size)
        setGuestItems(
          get().items.map((i) =>
            i.id === file.id
              ? { ...i, size, modified: new Date().toISOString() }
              : i
          )
        )
        return true
      }
      try {
        replace(await FileService.patchFile(file.id, content))
        return true
      } catch (error) {
        return fail(error) ?? false
      }
    }
  }
})

// языки нужны и гостю: шаблоны новых файлов и доступность запуска
useLanguagesStore.getState().load()
