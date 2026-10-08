import { useState } from "react"
import { toast } from "react-toastify"
import { AuthService } from "@/services/authService"
import { useOAuthProviders } from "@/hooks/useOAuthProviders"
import { errorMessage, useT, type MessageKey } from "@/i18n"
import styles from "./OAuthButtons.module.css"

/** Значок Яндекс ID: красный круг с «Я» (фирменный цвет #FC3F1D). */
const YandexIcon = () => (
  <svg width='22' height='22' viewBox='0 0 44 44' aria-hidden='true'>
    <circle cx='22' cy='22' r='22' fill='#FC3F1D' />
    <path
      fill='#fff'
      d='M24.76 34.84h4.66V9.16h-6.78c-6.82 0-10.4 3.5-10.4 8.67 0 4.12 1.97 6.55 5.48 9.07l-6.1 7.94h5.05l6.78-8.94-2.35-1.58c-2.85-1.93-4.24-3.43-4.24-6.67 0-2.85 2-4.78 5.8-4.78h2.1v21.97z'
    />
  </svg>
)

/** Значок VK: белый квадрат с буквами VK в цвет кнопки. */
const VkIcon = () => (
  <svg width='22' height='22' viewBox='0 0 24 24' aria-hidden='true'>
    <path
      fill='#fff'
      d='M15.684 0H8.316C1.592 0 0 1.592 0 8.316v7.368C0 22.408 1.592 24 8.316 24h7.368C22.408 24 24 22.408 24 15.684V8.316C24 1.592 22.391 0 15.684 0zm3.692 17.123h-1.744c-.66 0-.864-.525-2.05-1.727-1.033-1-1.49-1.135-1.744-1.135-.356 0-.458.102-.458.593v1.575c0 .424-.135.678-1.253.678-1.846 0-3.896-1.118-5.335-3.202C4.624 10.857 4.03 8.57 4.03 8.096c0-.254.102-.491.593-.491h1.744c.44 0 .61.203.78.678.863 2.49 2.303 4.675 2.896 4.675.22 0 .322-.102.322-.66V9.721c-.068-1.186-.695-1.287-.695-1.71 0-.204.17-.407.44-.407h2.744c.373 0 .508.203.508.643v3.473c0 .372.17.508.271.508.22 0 .407-.136.813-.542 1.254-1.406 2.151-3.574 2.151-3.574.119-.254.322-.491.763-.491h1.744c.525 0 .644.27.525.643-.22 1.017-2.354 4.031-2.354 4.031-.186.305-.254.44 0 .78.186.254.796.779 1.203 1.253.745.847 1.32 1.558 1.473 2.05.17.49-.085.744-.576.744z'
    />
  </svg>
)

const ICONS: Record<string, () => React.JSX.Element> = {
  yandex: YandexIcon,
  vk: VkIcon
}
const BRAND: Record<string, string> = { yandex: styles.yandex, vk: styles.vk }

/** Кнопки «Войти с …» в окне входа — по брендбукам Яндекс ID и VK ID. */
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
      {providers.map((p) => {
        const Icon = ICONS[p.id]
        return (
          <button
            key={p.id}
            className={`${styles.button} ${BRAND[p.id] ?? ""}`}
            disabled={disabled || busy !== null}
            onClick={() => go(p.id)}
          >
            {Icon && <Icon />}
            <span>{t(`oauth.button.${p.id}` as MessageKey)}</span>
          </button>
        )
      })}
    </div>
  )
}
