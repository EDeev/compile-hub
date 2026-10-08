import MainPage from "@/pages/MainPage"
import NotFoundPage from "@/pages/NotFoundPage"
import ResetPasswordPage from "@/pages/ResetPasswordPage"
import VerifyPage from "@/pages/VerifyPage"

export interface RouteConfig {
  path: string
  element: React.ReactNode
}

export const ROUTES = {
  MAIN: "/",
  PASSWORD_RESET: "/password-reset",
  VERIFY: "/verify"
}

export const routeConfig: RouteConfig[] = [
  { path: ROUTES.MAIN, element: <MainPage /> },
  { path: ROUTES.PASSWORD_RESET, element: <ResetPasswordPage /> },
  { path: ROUTES.VERIFY, element: <VerifyPage /> },
  { path: "*", element: <NotFoundPage /> }
]
