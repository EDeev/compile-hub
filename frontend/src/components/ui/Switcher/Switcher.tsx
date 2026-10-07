import styles from "./Switcher.module.css"
import { useState } from "react"

interface SwitcherProps {
  initialValue?: boolean
  onChange?: (value: boolean) => void
  ariaLabel?: string
}

export const Switcher = ({ initialValue = false, onChange }: SwitcherProps) => {
  const [isActive, setIsActive] = useState(initialValue)

  const toggleSwitch = () => {
    const newValue = !isActive
    setIsActive(newValue)
    onChange?.(newValue)
  }

  return (
    <button
      className={`${styles.switcherContainer} ${isActive ? styles.active : ""}`}
      onClick={toggleSwitch}
      aria-checked={isActive}
      role='switch'
      aria-label='switcher'
    >
      <span className={styles.switcherThumb} />
    </button>
  )
}
