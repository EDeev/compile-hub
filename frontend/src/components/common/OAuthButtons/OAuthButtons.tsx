import { useState } from "react"
import { toast } from "react-toastify"
import { useOAuthProviders } from "@/hooks/useOAuthProviders"
import { AuthService } from "@/services/authService"
import { errorMessage, useT } from "@/i18n"
import styles from "./OAuthButtons.module.css"

const BRAND: Record<string, string> = { yandex: styles.yandex, vk: styles.vk }

/** Кнопки «Войти через …» в окне входа. */
export const OAuthButtons = ({ disabled }: { disabled?: boolean }) => {
  const t = useT()
  const providers = useOAuthProviders()
  const [busy, setBusy] = useState<string | null>(null)
  if (providers.length === 0) return null

  const go = async (id: string) => {
    setBusy(id)
    try {
      await AuthService.oauthStart(id)
    } catch (error) {
      toast.error(errorMessage(error))
      setBusy(null)
    }
  }

  return (
    <div className={styles.block}>
      <div className={styles.or}>{t("oauth.or")}</div>
      {providers.map((p) => (
        <button
          key={p.id}
          className={`${styles.button} ${BRAND[p.id] ?? ""}`}
          disabled={disabled || busy !== null}
          onClick={() => go(p.id)}
        >
          {t("oauth.loginWith", { name: p.name })}
        </button>
      ))}
    </div>
  )
}
