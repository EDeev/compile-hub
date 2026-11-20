import { MdNightlightRound, MdLightMode } from "react-icons/md"
import { useThemeStore } from "@/store/themeStore"
import styles from "./ThemeSwitcher.module.css"
import { useState } from "react"
import { AuthService } from "@/services/authService"
import { useT } from "@/i18n"

type ThemeSwitcherProps = { className?: string }

export const ThemeSwitcher: React.FC<ThemeSwitcherProps> = ({ className }) => {
  const { theme, toggleTheme } = useThemeStore()
  const t = useT()
  const [isAnimating, setIsAnimating] = useState(false)

  const handleClick = () => {
    if (isAnimating) return

    setIsAnimating(true)
    setTimeout(() => {
      toggleTheme()
      AuthService.saveSettings({ theme: useThemeStore.getState().theme }).catch(
        () => {}
      )
      setIsAnimating(false)
    }, 400) // должно быть = fade в css-файле
  }

  return (
    // кнопка, а не span: доступна с клавиатуры (Tab, Enter/пробел) и называется для экранных читалок
    <button
      type='button'
      className={`${styles.switcher} ${className ?? ""}`.trim()}
      aria-label={t(theme === "dark" ? "theme.toLight" : "theme.toDark")}
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
    </button>
  )
}
