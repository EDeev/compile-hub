import { lazy, Suspense } from "react"
import styles from "./MainPage.module.css"
import { Filebar } from "@/components/common/Filebar/Filebar"
import { Welcome } from "@/components/common/Welcome"
import { useUserStore } from "@/store/userStore"
import { useEditorState } from "@/store/editorStore"

// редактор (CodeMirror) и консоль (xterm) — отдельный чанк: грузится, когда открыт файл
const loadEditor = () => import("@/components/common/Editor")
const Editor = lazy(() => loadEditor().then((m) => ({ default: m.Editor })))

export default function MainPage() {
  // при входе и выходе навигация по папкам начинается заново
  const userId = useUserStore((s) => s.currentUser.id)
  const hasFile = useEditorState((s) => s.currentFile !== null)
  return (
    // первое касание списка файлов — сигнал, что редактор скоро понадобится: подгрузить заранее
    <main
      className={styles.main}
      onPointerEnter={() => void loadEditor()}
      onFocus={() => void loadEditor()}
    >
      <h1 className='visually-hidden'>CompileHub — онлайн-компилятор</h1>
      <Filebar key={userId} />
      {hasFile ? (
        <Suspense fallback={<div className={styles.editorPlaceholder} />}>
          <Editor />
        </Suspense>
      ) : (
        <Welcome />
      )}
    </main>
  )
}
