import { useModalStore } from "@/store/modalStore"
import styles from "./ConfirmModal.module.css"
import { Button } from "@/components/ui/Button"
import { useT } from "@/i18n"

interface ConfirmModalProps {
  title: string
  type: "default" | "warning"
  message: string
  onConfirm: () => void
  onCancel: () => void
  className?: string
}

export const ConfirmModal: React.FC<ConfirmModalProps> = ({
  title = "Oops, something went wrong",
  type = "default",
  message,
  onConfirm,
  onCancel
}) => {
  const { closeModal } = useModalStore()
  const t = useT()

  return (
    <div className={styles.content}>
      <h2>{title}</h2>
      <p>{message}</p>
      <div className={styles.buttons}>
        <Button
          variant={type === "warning" ? "danger" : "primary"}
          onClick={() => {
            onConfirm()
            closeModal()
          }}
        >
          {t("common.ok")}
        </Button>
        <Button
          variant='secondary'
          onClick={() => {
            onCancel()
          }}
        >
          {t("common.cancel")}
        </Button>
      </div>
    </div>
  )
}
