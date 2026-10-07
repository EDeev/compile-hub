// src/App.tsx
import { BrowserRouter } from "react-router-dom"
import { AppRouter } from "@/router"
import { Modal } from "./components/ui/Modal"
import Header from "@/components/common/Header"

function App() {
  return (
    <BrowserRouter>
      <div className='app'>
        <Header />
        <AppRouter />
        <Modal />
      </div>
    </BrowserRouter>
  )
}

export default App
