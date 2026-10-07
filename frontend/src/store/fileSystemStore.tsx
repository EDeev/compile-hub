import { create } from "zustand"
import { type Item } from "@/types/fileSystem"
import { FileService } from "@/services/fileService"
import { useUserStore } from "./userStore"
import { GUEST_LIMITS } from "@/utils/constants"
import { useModalStore } from "@/store/modalStore"
import { ErrorModal } from "@/components/modals/ErrorModal"

/*
  tsX в этом файле испльзуется для передачи импортируемых комопнентов
  в openModal, например, openModal(<ErrorModal title='' message='' />) 
*/

interface useFileSystemStore {
  items: Item[]
  isLoading: boolean
  error: string | null
  guestLimitReached: boolean

  // Загрузка данных
  loadItems: (userId: string) => Promise<void>

  // Действия с файлами и папками
  setItems: (items: Item[]) => void
  addItem: (item: Item) => void
  updateItem: <T extends Item>(id: number, updated: Partial<T>) => void
  deleteItem: (id: number) => void
  moveItem: (id: number, targetFolderId: number | null) => void
}

const GUEST_STORAGE_KEY = "guest_files"

export const useFileSystemStore = create<useFileSystemStore>((set, get) => {
  // Сохранение файлов гостя в localStorage
  const saveGuestItems = (items: Item[]) => {
    const { currentUser } = useUserStore.getState()
    if (currentUser.isGuest) {
      localStorage.setItem(GUEST_STORAGE_KEY, JSON.stringify(items))
    }
  }

  // Проверка лимитов для гостя
  const checkGuestLimits = (newItem: Item) => {
    const { currentUser } = useUserStore.getState()
    if (!currentUser.isGuest) return false

    const { items } = get()
    const fileCount = items.filter((i) => i.type === "file").length
    const folderCount = items.filter((i) => i.type === "folder").length

    return (
      (newItem.type === "file" && fileCount >= GUEST_LIMITS.MAX_FILES) ||
      (newItem.type === "folder" && folderCount >= GUEST_LIMITS.MAX_FOLDERS)
    )
  }

  // Инициализация из localStorage для гостя
  const initializeItems = () => {
    const { currentUser } = useUserStore.getState()
    if (currentUser.isGuest) {
      const stored = localStorage.getItem(GUEST_STORAGE_KEY)
      return stored ? JSON.parse(stored) : []
    }
    return []
  }

  return {
    items: initializeItems(),
    isLoading: false,
    error: null,
    guestLimitReached: false,

    // Загрузка данных
    loadItems: async (userId) => {
      const { currentUser } = useUserStore.getState()

      // Для гостя не загружаем с сервера
      if (currentUser.isGuest) return

      set({ isLoading: true })
      try {
        const items = await FileService.fetchUserFiles(userId)
        set({ items, error: null })
      } catch (err) {
        set({ error: "Failed to load files" })
      } finally {
        set({ isLoading: false })
      }
    },

    // Установка элементов
    setItems: (items) => {
      const { currentUser } = useUserStore.getState()
      set({ items })
      if (currentUser.isGuest) saveGuestItems(items)
    },

    // Добавление элемента
    addItem: (item) => {
      const { currentUser } = useUserStore.getState()
      const { openModal } = useModalStore.getState()

      if (checkGuestLimits(item)) {
        set({ guestLimitReached: true })

        openModal(
          <ErrorModal
            title="You've reached guest limit"
            message={`Guest mode allows you to create only 
                    ${GUEST_LIMITS.MAX_FOLDERS} folders and
                     ${GUEST_LIMITS.MAX_FILES} files,
                      to do more, please login`}
          />
        )

        return
      }

      set((state) => {
        const newItems = [...state.items, item]
        if (currentUser.isGuest) saveGuestItems(newItems)
        return {
          items: newItems,
          guestLimitReached: false
        }
      })
    },

    // Обновление элемента
    updateItem: (id, updated) => {
      const { currentUser } = useUserStore.getState()

      set((state) => {
        const newItems = state.items.map((item) => {
          if (item.id !== id) return item

          // Для папок исключаем поле `folder`
          if (item.type === "folder") {
            const rest = { ...updated }
            if ("folder" in rest) delete rest.folder
            return { ...item, ...rest }
          }

          return { ...item, ...updated }
        })

        if (currentUser.isGuest) saveGuestItems(newItems)
        return { items: newItems }
      })
    },

    // Удаление элемента
    deleteItem: async (id) => {
      const { currentUser } = useUserStore.getState()
      const { items } = get()

      const newItems = items.filter((item) => item.id !== id)
      set({ items: newItems })
      if (currentUser.isGuest) saveGuestItems(newItems)

      try {
        if (!currentUser.isGuest) {
          await FileService.deleteFileOnServer(id)
        }
      } catch (err) {
        set({ items }) // Откат при ошибке
        if (currentUser.isGuest) saveGuestItems(items)
        throw new Error("Не удалось удалить файл")
      }
    },

    // Перемещение элемента
    moveItem: (id, targetFolderId) => {
      const { currentUser } = useUserStore.getState()

      set((state) => {
        const newItems = state.items.map((item) => {
          if (item.id !== id) return item
          if (item.type === "folder") return item // Папки не перемещаем
          // тут api вызов
          return { ...item, folder: targetFolderId }
        })

        if (currentUser.isGuest) saveGuestItems(newItems)
        return { items: newItems }
      })
    }
  }
})
