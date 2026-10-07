// src/router/AppRouter.tsx
import { type RouteObject, useRoutes } from 'react-router-dom'
import { routeConfig } from './routes'

export function AppRouter() {
  // Преобразуем нашу конфигурацию в формат, понятный React Router
  const routes: RouteObject[] = routeConfig.map(({ path, element }) => ({
    path,
    element,
  }))

  // useRoutes - хук React Router для создания маршрутов
  const element = useRoutes(routes)

  return element
}
