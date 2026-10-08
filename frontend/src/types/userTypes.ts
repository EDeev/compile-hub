import type { Limits, Usage } from "@/api/types"

export interface User {
  id: string
  email: string | null
  username: string
  isGuest: boolean
  emailVerified: boolean
  limits: Limits | null
  usage: Usage | null
}

export const GUEST_USER: User = {
  id: "guest_user",
  email: null,
  username: "Гость",
  isGuest: true,
  emailVerified: false,
  limits: null,
  usage: null
}
