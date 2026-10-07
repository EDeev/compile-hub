// src/pages/NotFoundPage/NotFoundPage.tsx
import { Link } from "react-router-dom"
import { ROUTES } from "@/router/routes"

export default function NotFoundPage() {
  return (
    <div className='not-found-page'>
      <h1>404 - Страница не найдена</h1>
      <p>Запрашиваемая страница не существует</p>
      <Link to={ROUTES.MAIN}>Вернуться на главную</Link>
    </div>
  )
}
