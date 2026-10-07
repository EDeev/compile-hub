import { create } from "zustand"
import { type Item } from "@/types/fileSystem"

interface FileStore {
  items: Item[]
  setItems: (items: Item[]) => void
  addItem: (item: Item) => void
  updateItem: (id: number, updated: Partial<Item>) => void
  deleteItem: (id: number) => void
  moveFile: (id: number, folderId: number | null) => void
}

export const useFileStore = create<FileStore>((set) => ({
  items: [],
  setItems: (items) => set({ items }),
  addItem: (item) =>
    set((state) => ({
      items: [...state.items, item]
    })),

  updateItem: (id, updated) =>
    set((state) => ({
      items: state.items.map((item) => {
        if (item.id !== id) return item

        // Безопасное обновление с проверкой типов
        if (item.type === "folder") {
          return {
            ...item,
            ...(updated.type === "folder" ? updated : {})
          }
        }

        return {
          ...item,
          ...updated,
          type: "file" // Гарантируем сохранение типа
        }
      })
    })),
  deleteItem: (id) =>
    set((state) => ({
      items: state.items.filter((item) => item.id !== id)
    })),
  moveFile: (id, folderId) =>
    set((state) => ({
      items: state.items.map((item) => {
        // Перемещаем только файлы
        if (item.id === id && item.type === "file") {
          return { ...item, folder: folderId }
        }
        return item
      })
    }))
}))

// updateItem: (id, updated) =>
//     set((state) => ({
//       items: state.items.map((item) => {
//         if (item.id !== id) return item

//         if (item.type === "folder") {
//           // возращаем новый объект без свойста folder т.к. нет вложенных папок
//           const { folder, ...rest } = updated as any // игонрируем типы для упрощения кода
//           return { ...item, ...rest }
//         }

//         return { ...item, ...updated }
//       })
//     }))
