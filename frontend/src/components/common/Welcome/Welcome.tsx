import { Button } from "@/components/ui/Button"
import { useUserStore } from "@/store/userStore"
import { useUiStore } from "@/store/uiStore"
import { useIsMobile } from "@/hooks/useIsMobile"
import { useT } from "@/i18n"
import styles from "../Editor/Editor.module.css"

/** Приветствие, пока файл не открыт — лёгкое, без CodeMirror и xterm. */
export const Welcome = () => {
  const t = useT()
  const username = useUserStore((s) => s.currentUser.username)
  const isMobile = useIsMobile()
  const setFilesOpen = useUiStore((s) => s.setFilesOpen)
  return (
    <div className={styles.helloMessage}>
      <h2>
        {t("editor.greeting", { name: "" })}
        <span>{username}</span>
      </h2>
      <p>{t(isMobile ? "editor.hintMobile" : "editor.hint")}</p>
      {isMobile && (
        <Button
          variant='secondary'
          className={styles.openFiles}
          onClick={() => setFilesOpen(true)}
        >
          {t("editor.openFiles")}
        </Button>
      )}
    </div>
  )
}
