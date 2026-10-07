import { MdNightlightRound, MdLightMode } from "react-icons/md"
import { useThemeStore } from "@/store/themeStore"
import styles from "./ThemeSwitcher.module.css"
import { useState } from "react"

/* prettier-ignore */
interface ThemeSwitcherProps extends React.HTMLAttributes<HTMLSpanElement> {}

export const ThemeSwitcher: React.FC<ThemeSwitcherProps> = ({ className }) => {
  const { theme, toggleTheme } = useThemeStore()
  const [isAnimating, setIsAnimating] = useState(false)

  const handleClick = () => {
    if (isAnimating) return

    setIsAnimating(true)
    setTimeout(() => {
      toggleTheme()
      setIsAnimating(false)
    }, 400) // должно быть = fade в css-файле
  }

  return (
    <span
      className={`${styles.switcher} ${className}`.trim()}
      onClick={handleClick}
    >
      <span
        className={`${styles.iconContainer} ${
          isAnimating ? styles.out : styles.in
        }`}
      >
        {theme === "dark" ? (
          <MdLightMode size={30} className={styles.icon} />
        ) : (
          <MdNightlightRound size={30} className={styles.icon} />
        )}
      </span>
    </span>
  )
}
