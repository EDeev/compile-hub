import { useEffect, useState } from "react"
import { toast } from "react-toastify"
import { Switcher } from "@/components/ui/Switcher"
import { Button } from "@/components/ui/Button"
import { Input } from "@/components/ui/Input"
import { useUserStore } from "@/store/userStore"
import { useModalStore } from "@/store/modalStore"
import { AuthService } from "@/services/authService"
import { FormValidators } from "@/utils/validators"
import { errorMessage, useLanguageStore, useT } from "@/i18n"
import styles from "./GeneralTab.module.css"
import RuFlag from "@assets/icons/ru-flag.svg"
import UsFlag from "@assets/icons/us-flag.svg"

export const GeneralTab = () => {
  const t = useT()
  const { currentUser } = useUserStore()
  const { closeModal } = useModalStore()
  const { language, setLanguage } = useLanguageStore()
  const [resent, setResent] = useState(false)
  const [current, setCurrent] = useState("")
  const [next, setNext] = useState("")

  useEffect(() => {
    if (!currentUser.isGuest) AuthService.refreshMe().catch(() => {}) // свежие лимиты и использование
  }, [currentUser.isGuest])

  const switchLanguage = (toEnglish: boolean) => {
    const value = toEnglish ? "en" : "ru"
    setLanguage(value)
    AuthService.saveSettings({ uiLanguage: value }).catch((e) =>
      toast.error(errorMessage(e))
    )
  }

  const resend = async () => {
    try {
      await AuthService.resendVerification()
      setResent(true)
    } catch (e) {
      toast.error(errorMessage(e))
    }
  }

  const changePassword = async () => {
    try {
      await AuthService.changePassword(current, next)
      setCurrent("")
      setNext("")
      toast.success(t("settings.passwordChanged"))
    } catch (e) {
      toast.error(errorMessage(e))
    }
  }

  const limits = currentUser.limits
  const usage = currentUser.usage
  const fmt = (v: number | null | undefined) =>
    v === null || v === undefined ? t("settings.unlimited") : v
  const nextCheck = next
    ? FormValidators.validatePassword(next)
    : { isValid: false, text: "" }

  return (
    <div className={styles.mainContainer}>
      <h3>{t("settings.generalTitle")}</h3>
      {!currentUser.isGuest && (
        <div className={styles.profileContainer}>
          <div className={styles.profileInfo}>
            <span className={styles.name}>{currentUser.username}</span>
            <span className={styles.id}>{currentUser.email}</span>
            <span
              className={
                currentUser.emailVerified ? styles.verified : styles.notVerified
              }
            >
              {t(
                currentUser.emailVerified
                  ? "settings.emailVerified"
                  : "settings.emailNotVerified"
              )}
              {!currentUser.emailVerified && (
                <button className='link' onClick={resend} disabled={resent}>
                  {" · "}
                  {t(resent ? "settings.resent" : "settings.resend")}
                </button>
              )}
            </span>
            {limits && usage && (
              <span className={styles.id}>
                {t("settings.usage", {
                  files: usage.files,
                  maxFiles: fmt(limits.maxFiles),
                  folders: usage.folders,
                  maxFolders: fmt(limits.maxFolders),
                  runs: `${usage.runsToday}/${fmt(limits.runsPerDay)}`
                })}
              </span>
            )}
          </div>
        </div>
      )}
      <div className={styles.optionContainer}>
        <span>{t("settings.language")}</span>
        <div className={styles.langSwitcher}>
          <img src={RuFlag} alt='RU' />
          <Switcher
            initialValue={language === "en"}
            onChange={switchLanguage}
          />
          <img src={UsFlag} alt='EN' />
        </div>
      </div>
      {!currentUser.isGuest && (
        <>
          <div className={styles.passwordContainer}>
            <span>{t("settings.changePassword")}</span>
            <Input
              type='password'
              placeholder={t("settings.currentPassword")}
              value={current}
              onChange={(e) => setCurrent(e.target.value)}
            />
            <Input
              type='password'
              placeholder={t("settings.newPassword")}
              value={next}
              message={next ? nextCheck : undefined}
              onChange={(e) => setNext(e.target.value)}
            />
            <Button
              variant='secondary'
              disabled={!current || !nextCheck.isValid}
              onClick={changePassword}
            >
              {t("settings.changePassword")}
            </Button>
          </div>
          <div className={styles.optionContainer}>
            <span>{t("settings.logout")}</span>
            <Button
              variant='danger'
              className={styles.logOutButton}
              onClick={() => {
                closeModal()
                AuthService.logout()
              }}
            >
              {t("account.logout")}
            </Button>
          </div>
        </>
      )}
    </div>
  )
}
