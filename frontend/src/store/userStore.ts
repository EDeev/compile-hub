import { create } from "zustand"
import { type User } from "@/types"
import { GUEST_USER } from "@/types/userTypes"
import type { ApiUser } from "@/api/types"

interface UserStore {
  currentUser: User
  isAuthenticated: boolean
  /** true, пока при запуске приложения восстанавливается сессия по refresh-cookie */
  isRestoring: boolean
  login: (user: ApiUser) => void
  logout: () => void
  setRestoring: (value: boolean) => void
}

export const toUser = (user: ApiUser): User => ({
  id: String(user.id),
  email: user.email,
  username: user.username,
  isGuest: false,
  emailVerified: user.emailVerified,
  limits: user.limits,
  usage: user.usage
})

// сессия живёт в httpOnly refresh-cookie, поэтому пользователя в localStorage не храним
export const useUserStore = create<UserStore>((set) => ({
  currentUser: GUEST_USER,
  isAuthenticated: false,
  isRestoring: true,
  login: (user) => set({ currentUser: toUser(user), isAuthenticated: true }),
  logout: () => set({ currentUser: GUEST_USER, isAuthenticated: false }),
  setRestoring: (value) => set({ isRestoring: value })
}))
