import { Switcher } from "@/components/ui/Switcher"
import { Button } from "@/components/ui/Button"
import { useUserStore } from "@/store/userStore"
import styles from "./GeneralTab.module.css"
import RuFlag from "@assets/icons/ru-flag.svg"
import UsFlag from "@assets/icons/us-flag.svg"

export const GeneralTab = () => {
  const { currentUser } = useUserStore()
  return (
    <div className={styles.mainContainer}>
      <h3>Общие настройки</h3>
      <div className={styles.profileContainer}>
        <div className={styles.profileImg}>
          <img src='' alt='' />
        </div>
        <div className={styles.profileInfo}>
          <span className={styles.name}>{currentUser?.username}</span>
          <span className={styles.id}>ID: {currentUser?.id}</span>
        </div>
      </div>
      <div className={styles.optionContainer}>
        <span>Language</span>
        {/* В пропс init value можно запихнуть настройку юзера и облачно синхронизировать*/}
        <div className={styles.langSwitcher}>
          <img src={RuFlag} alt='' />
          <Switcher />
          <img src={UsFlag} alt='' />
        </div>
      </div>
      <div className={styles.optionContainer}>
        <span>Log out</span>
        <Button variant='danger' className={styles.logOutButton}>
          Log out
        </Button>
      </div>
    </div>
  )
}
