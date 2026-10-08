import { Link } from "react-router-dom"
import { ROUTES } from "@/router/routes"
import { useT } from "@/i18n"

export default function NotFoundPage() {
  const t = useT()
  return (
    <div className='not-found-page'>
      <h1>404 — {t("notFound.title")}</h1>
      <Link to={ROUTES.MAIN}>{t("notFound.back")}</Link>
    </div>
  )
}
