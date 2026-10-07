import { useModalStore } from "@/store/modalStore"
import styles from "./ErrorModal.module.css"
import { Button } from "@/components/ui/Button"

interface ErrorModalProps {
  title: string
  message: string
  className?: string
}

export const ErrorModal: React.FC<ErrorModalProps> = ({
  title = "Oops, something went wrong",
  message
}) => {
  const { closeModal } = useModalStore()
  return (
    <div className={styles.content}>
      <h2>{title}</h2>
      <p>{message}</p>
      <Button variant='secondary' onClick={closeModal}>
        OK
      </Button>
    </div>
  )
}
