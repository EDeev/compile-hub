import styles from "./Button.module.css"

type ButtonVariant = "primary" | "secondary" | "danger"

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = "primary",
  className = "",
  ...props
}) => {
  const buttonClasses = [styles.button, styles[variant], className]
    .join(" ")
    .trim()

  return (
    <button className={buttonClasses} {...props}>
      {children}
    </button>
  )
}
