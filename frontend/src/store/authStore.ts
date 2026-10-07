// ПЕРЕИМЕНОВАТЬ В authModalStore.ts
// ВЕСЬ ФАЙЛ - ЭТО ВАЛИДАЦИЯ ОКНА АВТОРИЗАЦИИ, НЕ БОЛЕЕ

import { create } from "zustand"
import { createDebouncer } from "@/utils/debouncer"
import { FormValidators } from "@/utils/validators"
import { VALIDATION_RULES } from "@/utils/constants"

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
  setPassword: (password: string) => void
  setConfirmPassword: (confirmPassword: string) => void
  resetForm: () => void
  // submitForm: (mode: string) => Promise<[string, boolean]>
  isValid: (mode: string) => boolean
}

export const useAuthStore = create<AuthState>((set, get) => {
  const checkUsernameOnServer = async (username: string) => {
    // проверка если юзер напечатал ещё символы во время проверки на сервере
    const currentUsername = get().username

    set({ isValidating: true })

    // заглушка запроса на сервер

    try {
      console.log("Отправлен запрос на проверку с юзернеймом " + currentUsername)
      const response = await fetch(
        `http://95.31.185.229:9999/api/auth/check-username?username=${username}`,
        {
          method: "GET", // Указываем метод
          headers: {
            "Content-Type": "application/json"
          }
        }
      )

      const data = await response.json()

      if (!response.ok || !data.available) {
        set((state) => ({
          ...state,
          errors: {
            ...state.errors,
            username: {
              isAvialable: false,
              message: "HTTP error, try again later"
            }
          },
          isValidating: false
        }))
      }

      const isFree = data.available

      if (get().username !== currentUsername) return

      set((state) => ({
        ...state,
        errors: {
          ...state.errors,
          username: {
            isAvialable: isFree,
            message: isFree
              ? `Username ${currentUsername} is avialable`
              : `Username ${currentUsername} is already in use`
          }
        },
        isValidating: false
      }))
    } catch (error) {
      // Вывести сообщ об ошибке
    }

    // вторая проверка после запроса на сервер
  }
  //   await fetch(`запрос на сервер c username`)
  //     .then(res => res.json())
  //     .then(data => data.available);

  const debounceDelay = VALIDATION_RULES.TIMING.DEBOUNCE_DELAY
  const usernameDebouncer = createDebouncer(checkUsernameOnServer, debounceDelay)

  return {
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
    isValidating: false,
    errors: {
      username: { isAvialable: false, message: "" },
      email: "",
      password: "",
      confirmPassword: ""
    },

    setUsername: (username: string, isReg: boolean) => {
      const { isValid, text } = FormValidators.validateUsername(username)

      set((state) => ({
        username,
        errors: {
          ...state.errors,
          username: { isAvialable: isValid, message: text }
        },
        isValidating: isValid && isReg ? true : false
      }))

      if (!isValid || !isReg) {
        usernameDebouncer.cancel()
        return
      }

      usernameDebouncer.check(username)
    },

    setEmail: (email: string) =>
      set((state) => ({
        email,
        errors: {
          ...state.errors,
          email: FormValidators.validateEmail(email).text
        }
      })),

    setPassword: (password: string) =>
      set((state) => {
        const passwordError = FormValidators.validatePassword(password).text
        let confirmError = ""

        if (state.confirmPassword && state.confirmPassword !== password) {
          confirmError = "Passwords don't match"
        }

        return {
          password,
          errors: {
            ...state.errors,
            password: passwordError,
            confirmPassword: confirmError
          }
        }
      }),

    setConfirmPassword: (confirmPassword: string) =>
      set((state) => ({
        confirmPassword,
        errors: {
          ...state.errors,
          confirmPassword: state.password !== confirmPassword ? "Passwords don't match" : ""
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
        errors: {
          username: { isAvialable: true, message: "" },
          email: "",
          password: "",
          confirmPassword: ""
        }
      })
    },
    // submitForm: async (mode: string) => {
    //   // mode будем передавать на сервер
    //   await new Promise((resolve) => setTimeout(resolve, 1500))
    //   return ["You're successfully signed up", false] as [string, boolean] // заглушка
    // },

    isValid: (mode: string): boolean => {
      const state = get()

      if (mode === "register") {
        return (
          state.errors.username.isAvialable &&
          !state.errors.email &&
          !state.errors.password &&
          !state.errors.confirmPassword &&
          !!state.username &&
          !!state.email &&
          !!state.password &&
          !!state.confirmPassword &&
          !state.isValidating
        )
      } else {
        return (
          state.errors.username.isAvialable &&
          !state.errors.password &&
          !!state.username &&
          !!state.password
        )
      }
    }
  }
})
