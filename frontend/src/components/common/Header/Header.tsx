import { MdMenu } from "react-icons/md"
import { useModalStore } from "@/store/modalStore"
import { Button } from "@/components/ui/Button"
import { Logo } from "@/components/ui/Logo"
import { Account } from "@/components/common/Account"
import { ThemeSwitcher } from "@/components/ui/ThemeSwitcher"
import { AuthModal } from "@/components/modals/AuthModal"
import { useUserStore } from "@/store/userStore"
import { useUiStore } from "@/store/uiStore"
import { useIsMobile } from "@/hooks/useIsMobile"
import { useT } from "@/i18n"
import styles from "./Header.module.css"

export default function Header() {
  const t = useT()
  const { openModal } = useModalStore()
  const { currentUser, isRestoring } = useUserStore()
  const { filesOpen, setFilesOpen } = useUiStore()
  const isMobile = useIsMobile()

  return (
    <header className={styles.header}>
      <div className={styles.headerContainer}>
        <div className={styles.headerLeft}>
          {isMobile && (
            <button
              className={styles.menuButton}
              aria-label='files'
              onClick={() => setFilesOpen(!filesOpen)}
            >
              <MdMenu size={26} />
            </button>
          )}
          <a href='/'>
            <Logo variant={isMobile ? "compact" : "standart"} />
          </a>
        </div>
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
                {/* на телефоне регистрация — переключателем в окне входа */}
                {!isMobile && (
                  <Button
                    variant='primary'
                    onClick={() =>
                      openModal(<AuthModal isReg={true} className='auth' />)
                    }
                  >
                    {t("header.signup")}
                  </Button>
                )}
              </>
            ) : (
              <Account />
            ))}
        </div>
      </div>
    </header>
  )
}
