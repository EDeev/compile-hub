import { create } from "zustand"
import { persist } from "zustand/middleware"
import { type User } from "@/types"
import { GUEST_USER } from "@/types/userTypes"

interface UserStore {
  currentUser: User
  isAuthenticated: boolean
  login: (userData: User) => void
  logout: () => void
  updateUser: (userData: Partial<User>) => void
}

export const useUserStore = create<UserStore>()(
  persist(
    (set) => ({
      currentUser: GUEST_USER,
      isAuthenticated: false,

      login: (userData) =>
        set({
          currentUser: userData,
          isAuthenticated: true
        }),

      logout: () =>
        set({
          currentUser: GUEST_USER,
          isAuthenticated: false
        }),

      updateUser: (userData) =>
        set((state) => ({
          currentUser: { ...state.currentUser, ...userData }
        }))
    }),
    {
      name: "user-storage",
      partialize: (state) => ({
        currentUser: state.currentUser.isGuest ? null : state.currentUser,
        isAuthenticated: state.isAuthenticated
      }),
      onRehydrateStorage: () => (state, error) => {
        if (error) {
          console.error("Error during rehydration:", error)
          return
        }

        if (!state?.currentUser) {
          return {
            currentUser: GUEST_USER,
            isAuthenticated: false
          }
        }
      }
    }
  )
)
