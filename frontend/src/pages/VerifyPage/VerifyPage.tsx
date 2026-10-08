import { useEffect, useRef, useState } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { ROUTES } from "@/router/routes"
import { AuthService } from "@/services/authService"
import { errorMessage, useT } from "@/i18n"
import styles from "../ResetPasswordPage/ResetPasswordPage.module.css"

/** Ссылка из письма подтверждения: /verify?token=… */
export default function VerifyPage() {
  const t = useT()
  const [params] = useSearchParams()
  const [state, setState] = useState<{ ok: boolean | null; text: string }>({
    ok: null,
    text: ""
  })
  const sent = useRef(false)

  useEffect(() => {
    if (sent.current) return // StrictMode вызывает эффект дважды, а токен одноразовый
    sent.current = true
    const token = params.get("token")
    if (!token) {
      setState({ ok: false, text: errorMessage({ code: "invalid_token" }) })
      return
    }
    AuthService.verify(token)
      .then(() => setState({ ok: true, text: t("verify.ok") }))
      .catch((error) => setState({ ok: false, text: errorMessage(error) }))
  }, [params, t])

  return (
    <div className={styles.wrapper}>
      <div className={styles.content}>
        <h2>{t("verify.title")}</h2>
        <h1>{state.ok === null ? t("verify.progress") : state.text}</h1>
        <Link to={ROUTES.MAIN} className='link'>
          {t("verify.toMain")}
        </Link>
      </div>
    </div>
  )
}
