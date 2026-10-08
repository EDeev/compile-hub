import { useModalStore } from "@/store/modalStore"
import { Button } from "@/components/ui/Button"
import { Logo } from "@/components/ui/Logo"
import { Account } from "@/components/common/Account"
import { ThemeSwitcher } from "@/components/ui/ThemeSwitcher"
import { AuthModal } from "@/components/modals/AuthModal"
import { useUserStore } from "@/store/userStore"
import { useT } from "@/i18n"
import styles from "./Header.module.css"

export default function Header() {
  const t = useT()
  const { openModal } = useModalStore()
  const { currentUser, isRestoring } = useUserStore()

  return (
    <header className={styles.header}>
      <div className={styles.headerContainer}>
        <a href='/'>
          <Logo variant='standart' />
        </a>
        <div className={styles.headerButtons}>
          <ThemeSwitcher className={styles.themeSwitcher} />
          {!isRestoring &&
            (currentUser.isGuest ? (
              <>
                <Button
                  variant='secondary'
                  onClick={() => openModal(<AuthModal />)}
                >
                  {t("header.login")}
                </Button>
                <Button
                  variant='primary'
                  onClick={() =>
                    openModal(<AuthModal isReg={true} className='auth' />)
                  }
                >
                  {t("header.signup")}
                </Button>
              </>
            ) : (
              <Account />
            ))}
        </div>
      </div>
    </header>
  )
}
