import { lazy, Suspense } from "react"
import styles from "./MainPage.module.css"
import { Filebar } from "@/components/common/Filebar/Filebar"
import { useUserStore } from "@/store/userStore"

// редактор (CodeMirror) и консоль (xterm) — отдельный чанк: первая отрисовка не ждёт ~700 КБ скриптов
const Editor = lazy(() =>
  import("@/components/common/Editor").then((m) => ({ default: m.Editor }))
)

export default function MainPage() {
  // при входе и выходе навигация по папкам начинается заново
  const userId = useUserStore((s) => s.currentUser.id)
  return (
    <main className={styles.main}>
      <h1 className='visually-hidden'>CompileHub — онлайн-компилятор</h1>
      <Filebar key={userId} />
      <Suspense fallback={<div className={styles.editorPlaceholder} />}>
        <Editor />
      </Suspense>
    </main>
  )
}
