export interface User {
  id: string | "guest"
  email: string | null
  username: string
  token: string | null
  isGuest: boolean
}

export const GUEST_USER: User = {
  id: "guest_user",
  email: null,
  username: "Гость",
  token: null,
  isGuest: true
}
