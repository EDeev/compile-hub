// src/store/clickDragStore.ts
import { create } from "zustand"

import { type Item } from "@/types"

interface ClickDragStore {
  selectedItem: Item | null
  isDragMode: boolean
  selectForMove: (item: Item) => void
  cancelMove: () => void
  isSelected: (itemId: number) => boolean
}

export const useClickDragStore = create<ClickDragStore>((set, get) => ({
  selectedItem: null,
  isDragMode: false,

  selectForMove: (item) => {
    console.log("Selecting for move:", item.name) // Для отладки
    set({ selectedItem: item, isDragMode: true })
  },

  cancelMove: () => {
    set({ selectedItem: null, isDragMode: false })
  },

  isSelected: (itemId) => get().selectedItem?.id === itemId
}))
