import { Link } from "react-router-dom"
import { ROUTES } from "@/router/routes"
import { Logo } from "@/components/ui/Logo"
import { useModalStore } from "@/store/modalStore"
import { AuthForm } from "./AuthForm"
import { OAuthButtons } from "@/components/common/OAuthButtons"
import { useAuthForm } from "@/hooks/useAuthForm"
import styles from "./AuthModal.module.css"
import { useT } from "@/i18n"

interface AuthModalProps {
  className?: string
  isReg?: boolean
}

export const AuthModal: React.FC<AuthModalProps> = ({ isReg = false }) => {
  const {
    mode,
    setMode,
    isLoading,
    isValidating,
    statusMessage,
    username,
    email,
    password,
    confirmPassword,
    errors,
    setUsername,
    setEmail,
    setPassword,
    setConfirmPassword,
    handleSubmit
  } = useAuthForm(isReg ? "register" : "login")

  const { closeModal } = useModalStore()
  const t = useT()

  return (
    <div className={styles.content}>
      <Logo variant='compact' />
      <h3>{t("auth.welcome")}</h3>
      <AuthForm
        mode={mode}
        isLoading={isLoading}
        isValidating={isValidating}
        errors={errors}
        values={{ username, email, password, confirmPassword }}
        onChange={{
          username: (v) => setUsername(v, mode === "register"),
          email: setEmail,
          password: (v) => setPassword(v, mode === "register"),
          confirmPassword: setConfirmPassword
        }}
        onSubmit={handleSubmit}
        onToggleMode={() => setMode(mode === "login" ? "register" : "login")}
        statusMessage={statusMessage}
      />
      <OAuthButtons disabled={isLoading} />
      <Link
        to={ROUTES.PASSWORD_RESET}
        className={`link ${styles.forgotPassword}`}
        onClick={closeModal}
      >
        {t("auth.forgot")}
      </Link>
    </div>
  )
}
