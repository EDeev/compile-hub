import { useSyncExternalStore } from "react"

export const MOBILE_QUERY = "(max-width: 768px)"

const subscribe = (onChange: () => void) => {
  const mql = window.matchMedia(MOBILE_QUERY)
  mql.addEventListener("change", onChange)
  return () => mql.removeEventListener("change", onChange)
}

/** Узкий экран (телефон, маленький планшет) — своя раскладка: файлы выдвижной панелью, редактор вкладками. */
export const useIsMobile = () =>
  useSyncExternalStore(subscribe, () => window.matchMedia(MOBILE_QUERY).matches)
