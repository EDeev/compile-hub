import { useEffect, useState } from "react"
import type { OAuthProvider } from "@/api/types"
import { AuthService } from "@/services/authService"

let cache: OAuthProvider[] | null = null

/** Включённые сервисы входа (Яндекс, VK ID) — запрашиваются один раз за открытие страницы. */
export const useOAuthProviders = () => {
  const [providers, setProviders] = useState<OAuthProvider[]>(cache ?? [])
  useEffect(() => {
    if (cache) return
    AuthService.oauthProviders()
      .then((list) => {
        cache = list
        setProviders(list)
      })
      .catch(() => {})
  }, [])
  return providers
}
