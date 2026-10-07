import { Input } from "@/components/ui/Input"
import { Button } from "@/components/ui/Button"
import { MdLockOutline, MdMailOutline, MdPersonOutline } from "react-icons/md"
import { CgSpinner } from "react-icons/cg"
import styles from "./AuthModal.module.css"

interface AuthFormProps {
  mode: "login" | "register"
  isLoading: boolean
  isValidating: boolean
  errors: any
  values: {
    username: string
    email: string
    password: string
    confirmPassword: string
  }
  onChange: {
    username: (v: string) => void
    email: (v: string) => void
    password: (v: string) => void
    confirmPassword: (v: string) => void
  }
  onSubmit: () => void
  onToggleMode: () => void
  statusMessage: { text: string; isSuccess: boolean }
}

export const AuthForm: React.FC<AuthFormProps> = ({
  mode,
  isLoading,
  isValidating,
  errors,
  values,
  onChange,
  onSubmit,
  onToggleMode,
  statusMessage
}) => {
  return (
    <div className={styles.authForm}>
      <Input
        type='text'
        autoFocus
        className={`${errors.username.isAvialable ? "success" : "error"} ${styles.input}`}
        isRequired
        isValidating={isValidating}
        icon={<MdPersonOutline />}
        placeholder='Enter username'
        disabled={isLoading}
        value={values.username}
        onChange={(e) => onChange.username(e.target.value)}
        message={{
          isValid: errors.username.isAvialable,
          text: errors.username.message
        }}
        name='username'
      />
      {mode === "register" && (
        <Input
          type='email'
          className={styles.input}
          isRequired
          icon={<MdMailOutline />}
          placeholder='Enter email'
          disabled={isLoading}
          value={values.email}
          onChange={(e) => onChange.email(e.target.value)}
          message={{ isValid: false, text: errors.email }}
          name='email'
        />
      )}
      <Input
        type='password'
        className={styles.input}
        isRequired
        icon={<MdLockOutline />}
        placeholder='Enter password'
        disabled={isLoading}
        value={values.password}
        onChange={(e) => onChange.password(e.target.value)}
        message={{ isValid: false, text: errors.password }}
        name='password'
      />
      {mode === "register" && (
        <Input
          type='password'
          className={styles.input}
          isRequired
          icon={<MdLockOutline />}
          placeholder='Confirm password'
          disabled={isLoading}
          value={values.confirmPassword}
          onChange={(e) => onChange.confirmPassword(e.target.value)}
          message={{ isValid: false, text: errors.confirmPassword }}
          name='confirm password'
        />
      )}

      <div className={styles.buttonGroup}>
        <p
          className={`${styles.statusMessage} ${styles[statusMessage.isSuccess ? "green" : "red"]}`}
        >
          {statusMessage.text || "\u00A0"}
        </p>
        <Button
          variant={mode === "register" ? "secondary" : "primary"}
          disabled={isLoading || isValidating}
          onClick={() => (mode === "register" ? onToggleMode() : onSubmit())}
        >
          {isLoading && mode === "login" ? (
            <CgSpinner size={25} className={styles.buttonLoadSpinner} />
          ) : (
            "Log In"
          )}
        </Button>
        <Button
          variant={mode === "register" ? "primary" : "secondary"}
          style={{ order: mode === "register" ? 0 : -1 }}
          disabled={
            isLoading ||
            isValidating ||
            (!errors.username.isAvialable && mode === "register")
          }
          onClick={() => (mode === "login" ? onToggleMode() : onSubmit())}
        >
          {isLoading && mode === "register" ? (
            <CgSpinner size={25} className={styles.buttonLoadSpinner} />
          ) : (
            "Sign Up"
          )}
        </Button>
      </div>
    </div>
  )
}
