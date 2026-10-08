import { useEffect } from "react"
import { BrowserRouter } from "react-router-dom"
import { ToastContainer } from "react-toastify"
import "react-toastify/dist/ReactToastify.css"
import { AppRouter } from "@/router"
import { Modal } from "./components/ui/Modal"
import Header from "@/components/common/Header"
import { AuthService } from "@/services/authService"
import { useThemeStore } from "@/store/themeStore"
import { useLanguageStore } from "@/i18n"

function App() {
  const theme = useThemeStore((s) => s.theme)

  useEffect(() => {
    document.documentElement.lang = useLanguageStore.getState().language
    AuthService.restore()
  }, [])

  return (
    <BrowserRouter>
      <div className='app'>
        <Header />
        <AppRouter />
        <Modal />
        <ToastContainer
          position='bottom-right'
          theme={theme}
          autoClose={4000}
          newestOnTop
        />
      </div>
    </BrowserRouter>
  )
}

export default App
