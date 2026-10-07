import styles from "./Logo.module.css"
import logoImage from "@/assets/logo.svg"

type LogoVariant = "standart" | "compact"

interface LogoProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: LogoVariant
}

export const Logo: React.FC<LogoProps> = ({
  variant = "standart",
  ...props
}) => {
  const logoClasses = [styles.logo, styles[variant]].join(" ").trim()

  return (
    <div className={logoClasses} {...props} tabIndex={1}>
      <img src={logoImage} alt='logo' />
      <span>CompileHub</span>
    </div>
  )
}
