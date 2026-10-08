import { useState } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { ROUTES } from "../../router/routes"
import { Input } from "@/components/ui/Input"
import { Button } from "@/components/ui/Button"
import { MdLockOutline, MdMailOutline } from "react-icons/md"
import styles from "./ResetPasswordPage.module.css"
import { FormValidators } from "@/utils/validators"
import { useModalStore } from "@/store/modalStore"
import { AuthModal } from "@/components/modals/AuthModal"
import { AuthService } from "@/services/authService"
import { errorMessage, useT } from "@/i18n"

type Message = { isValid: boolean; text: string }

/** Без ?token — запрос ссылки на почту; с ?token (ссылка из письма) — ввод нового пароля. */
export default function ResetPasswordPage() {
  const t = useT()
  const [params] = useSearchParams()
  const token = params.get("token")
  const { openModal } = useModalStore()
  const [value, setValue] = useState("")
  const [message, setMessage] = useState<Message>({ isValid: true, text: "" })
  const [done, setDone] = useState(false)
  const [busy, setBusy] = useState(false)

  const submit = async () => {
    const check = token
      ? FormValidators.validatePassword(value)
      : FormValidators.validateEmail(value)
    setMessage(check)
    if (!check.isValid) return
    setBusy(true)
    try {
      await (token
        ? AuthService.resetPassword(token, value)
        : AuthService.forgotPassword(value))
      setDone(true)
    } catch (error) {
      setMessage({ isValid: false, text: errorMessage(error) })
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className={styles.wrapper}>
      <div className={styles.content}>
        {done ? (
          <h1>{token ? t("reset.done") : t("reset.sent", { email: value })}</h1>
        ) : (
          <>
            <h2>{t(token ? "reset.newTitle" : "reset.title")}</h2>
            <div className={styles.inputGroup}>
              <Input
                type={token ? "password" : "email"}
                icon={token ? <MdLockOutline /> : <MdMailOutline />}
                className={styles.inputContainer}
                placeholder={t(
                  token ? "settings.newPassword" : "reset.emailPlaceholder"
                )}
                message={message}
                value={value}
                disabled={busy}
                onChange={(e) => setValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") submit()
                }}
              />
              <Button onClick={submit} disabled={busy}>
                {t(token ? "reset.save" : "reset.send")}
              </Button>
            </div>
          </>
        )}
        <Link
          to={ROUTES.MAIN}
          className={`${done ? styles.submitted : ""} link`}
          onClick={() => openModal(<AuthModal />)}
        >
          {t("auth.login")}
        </Link>
      </div>
    </div>
  )
}
