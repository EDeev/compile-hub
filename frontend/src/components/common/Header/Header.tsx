import { useModalStore } from "@/store/modalStore"
import { Button } from "@/components/ui/Button"
import { Logo } from "@/components/ui/Logo"
import { Account } from "@/components/common/Account"
import { ThemeSwitcher } from "@/components/ui/ThemeSwitcher"
import { AuthModal } from "@/components/modals/AuthModal"
import styles from "./Header.module.css"

export default function Header() {
  const { openModal } = useModalStore()

  return (
    <header className={styles.header}>
      <div className={styles.headerContainer}>
        <a href='/'>
          <Logo variant='standart' />
        </a>
        <div className={styles.headerButtons}>
          <ThemeSwitcher className={styles.themeSwitcher} />
          <Button variant='secondary' onClick={() => openModal(<AuthModal />)}>
            Log In
          </Button>
          <Button
            variant='primary'
            onClick={() =>
              openModal(<AuthModal isReg={true} className='auth' />)
            }
          >
            Sign Up
          </Button>
          <Account />
        </div>
      </div>
    </header>
  )
}
