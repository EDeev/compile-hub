import styles from "./Modal.module.css"
import { useModalStore } from "@/store/modalStore"
import { useRef, useEffect } from "react"

export const Modal = () => {
  const { isOpen, isLocked, content, closeModal } = useModalStore()
  const modalRef = useRef<HTMLDivElement>(null)

  const mouseDownTarget = useRef<EventTarget | null>(null)

  // обработчик Esc
  useEffect(() => {
    if (!isOpen) return

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !isLocked) {
        closeModal()
      }
    }

    document.addEventListener("keydown", handleKeyDown)
    return () => document.removeEventListener("keydown", handleKeyDown)
  }, [isOpen, isLocked, closeModal])

  /*
    событие нажатие юзаем чтобы пофиксить баг, при котором при 
    зажатии лкм на окне, переведении курсора на бэкдроп и отпускании 
    мыши окно закрывалось 
  */

  const handleMouseDown = (e: React.MouseEvent) => {
    mouseDownTarget.current = e.target
  }

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (
      e.target === modalRef.current &&
      mouseDownTarget.current === modalRef.current &&
      !isLocked
    ) {
      closeModal()
    }

    mouseDownTarget.current = null
  }

  if (!isOpen || !content) return null

  return (
    <div
      ref={modalRef}
      className={styles.modal}
      onMouseDown={handleMouseDown}
      onClick={handleBackdropClick}
    >
      {content}
    </div>
  )
}
