// Состояние и проверка полей окна входа/регистрации
import { create } from "zustand"
import { createDebouncer } from "@/utils/debouncer"
import { FormValidators } from "@/utils/validators"
import { VALIDATION_RULES } from "@/utils/constants"
import { AuthService } from "@/services/authService"
import { errorMessage, t } from "@/i18n"

interface AuthState {
  username: string
  email: string
  password: string
  confirmPassword: string
  errors: {
    username: { isAvialable: boolean; message: string }
    email: string
    password: string
    confirmPassword: string
  }
  isValidating: boolean
  setUsername: (username: string, isReg: boolean) => void
  setEmail: (email: string) => void
  setPassword: (password: string, isReg: boolean) => void
  setConfirmPassword: (confirmPassword: string) => void
  resetForm: () => void
  isValid: (mode: string) => boolean
}

const emptyErrors = () => ({
  username: { isAvialable: false, message: "" },
  email: "",
  password: "",
  confirmPassword: ""
})

export const useAuthStore = create<AuthState>((set, get) => {
  const checkUsernameOnServer = async (username: string) => {
    try {
      const isFree = await AuthService.checkUsername(username)
      if (get().username !== username) return // пока ждали ответ, имя изменилось
      set((state) => ({
        errors: {
          ...state.errors,
          username: {
            isAvialable: isFree,
            message: t(isFree ? "auth.usernameFree" : "auth.usernameTaken", { name: username })
          }
        },
        isValidating: false
      }))
    } catch (error) {
      if (get().username !== username) return
      set((state) => ({
        errors: { ...state.errors, username: { isAvialable: false, message: errorMessage(error) } },
        isValidating: false
      }))
    }
  }

  const usernameDebouncer = createDebouncer(
    checkUsernameOnServer,
    VALIDATION_RULES.TIMING.DEBOUNCE_DELAY
  )

  return {
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
    isValidating: false,
    errors: emptyErrors(),

    setUsername: (username, isReg) => {
      // при входе поле принимает имя или почту — формат не проверяем
      const { isValid, text } = isReg
        ? FormValidators.validateUsername(username)
        : { isValid: username.length > 0, text: "" }
      set((state) => ({
        username,
        errors: { ...state.errors, username: { isAvialable: isValid, message: text } },
        isValidating: isValid && isReg
      }))
      if (!isValid || !isReg) {
        usernameDebouncer.cancel()
        return
      }
      usernameDebouncer.check(username)
    },

    setEmail: (email) =>
      set((state) => ({
        email,
        errors: { ...state.errors, email: FormValidators.validateEmail(email).text }
      })),

    setPassword: (password, isReg) =>
      set((state) => ({
        password,
        errors: {
          ...state.errors,
          // при входе правила сложности не проверяем — у старых паролей они могли быть другими
          password: isReg ? FormValidators.validatePassword(password).text : "",
          confirmPassword:
            state.confirmPassword && state.confirmPassword !== password
              ? t("validation.passwordsMismatch")
              : ""
        }
      })),

    setConfirmPassword: (confirmPassword) =>
      set((state) => ({
        confirmPassword,
        errors: {
          ...state.errors,
          confirmPassword:
            state.password !== confirmPassword ? t("validation.passwordsMismatch") : ""
        }
      })),

    resetForm: () => {
      usernameDebouncer.cancel()
      set({
        username: "",
        email: "",
        password: "",
        confirmPassword: "",
        isValidating: false,
        errors: emptyErrors()
      })
    },

    isValid: (mode) => {
      const s = get()
      if (mode === "register") {
        return (
          s.errors.username.isAvialable &&
          !s.errors.email &&
          !s.errors.password &&
          !s.errors.confirmPassword &&
          !!s.username &&
          !!s.email &&
          !!s.password &&
          !!s.confirmPassword &&
          !s.isValidating
        )
      }
      return !!s.username && !!s.password
    }
  }
})
