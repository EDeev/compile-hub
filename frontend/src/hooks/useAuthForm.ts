import { useEffect, useState } from "react"
import { toast } from "react-toastify"
import { useAuthStore } from "@/store/authStore"
import { useModalStore } from "@/store/modalStore"
import { AuthService } from "@/services/authService"
import { errorMessage, t } from "@/i18n"

export const useAuthForm = (initialMode: "login" | "register") => {
  const [mode, setMode] = useState<"login" | "register">(initialMode)
  const [isLoading, setIsLoading] = useState(false)
  const [statusMessage, setStatusMessage] = useState<{ text: string; isSuccess: boolean }>({
    text: "",
    isSuccess: true
  })

  const store = useAuthStore()
  const { setIsLocked, closeModal } = useModalStore()

  useEffect(() => {
    store.resetForm()
    setStatusMessage({ text: "", isSuccess: true })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode])

  const handleSubmit = async () => {
    if (!store.isValid(mode)) return
    setIsLocked(true)
    setIsLoading(true)
    try {
      if (mode === "login") {
        await AuthService.login(store.username, store.password)
        toast.success(t("auth.loggedIn"))
      } else {
        await AuthService.register(store.username, store.email, store.password)
        toast.success(t("auth.registered"), { autoClose: 8000 })
      }
      store.resetForm()
      setIsLocked(false)
      closeModal()
    } catch (error) {
      setStatusMessage({ text: errorMessage(error), isSuccess: false })
    } finally {
      setIsLoading(false)
      setIsLocked(false)
    }
  }

  return {
    mode,
    setMode,
    isLoading,
    isValidating: store.isValidating,
    statusMessage,
    username: store.username,
    email: store.email,
    password: store.password,
    confirmPassword: store.confirmPassword,
    errors: store.errors,
    setUsername: store.setUsername,
    setEmail: store.setEmail,
    setPassword: store.setPassword,
    setConfirmPassword: store.setConfirmPassword,
    handleSubmit
  }
}
