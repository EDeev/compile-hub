import { create } from "zustand"

type ModalStore = {
  isOpen: boolean
  isLocked: boolean
  content: React.ReactElement | null
  openModal: (content: React.ReactElement) => void
  setIsLocked: (state: boolean) => void
  closeModal: () => void
}

export const useModalStore = create<ModalStore>((set, get) => ({
  isOpen: false,
  isLocked: false,
  content: null,
  type: "info",
  openModal: (content) => set({ isOpen: true, content: content }),
  setIsLocked: (state) => {
    set({ isLocked: state })
  },
  closeModal: () => {
    if (!get().isLocked) {
      set({ isOpen: false, content: null, isLocked: false })
    }
  }
}))
