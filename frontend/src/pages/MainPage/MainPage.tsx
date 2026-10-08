import styles from "./MainPage.module.css"
import { Filebar } from "@/components/common/Filebar/Filebar"
import { Editor } from "@/components/common/Editor"
import { useUserStore } from "@/store/userStore"

export default function MainPage() {
  // при входе и выходе навигация по папкам начинается заново
  const userId = useUserStore((s) => s.currentUser.id)
  return (
    <main className={styles.main}>
      <h1 className='visually-hidden'>CompileHub — онлайн-компилятор</h1>
      <Filebar key={userId} />
      <Editor />
    </main>
  )
}
