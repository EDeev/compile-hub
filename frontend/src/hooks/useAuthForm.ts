import { useEffect, useState } from "react"
import { useAuthStore } from "@/store/authStore"
import { useModalStore } from "@/store/modalStore"
import { AuthService } from "@/services/authService"

export const useAuthForm = (initialMode: "login" | "register") => {
  const [mode, setMode] = useState<"login" | "register">(initialMode)
  const [isLoading, setIsLoading] = useState(false)
  const [statusMessage, setStatusMessage] = useState<{ text: string; isSuccess: boolean }>({
    text: "",
    isSuccess: true
  })

  const {
    username,
    email,
    password,
    confirmPassword,
    errors,
    isValidating,
    setUsername,
    setEmail,
    setPassword,
    setConfirmPassword,
    resetForm,
    isValid
  } = useAuthStore()

  const { setIsLocked } = useModalStore()

  useEffect(() => {
    resetForm()
    setStatusMessage({ text: "", isSuccess: true })
  }, [mode])

  const handleSubmit = async () => {
    if (!isValid(mode)) return

    setIsLocked(true)
    setIsLoading(true)
    try {
      const result =
        mode === "login"
          ? await AuthService.login({ username, password })
          : await AuthService.register({ username, email, password })

      const [text, success]: [string, boolean] = result
      if (success) resetForm()
      setStatusMessage({ text, isSuccess: success })
    } finally {
      setIsLoading(false)
      setIsLocked(false)
    }
  }

  return {
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
  }
}
