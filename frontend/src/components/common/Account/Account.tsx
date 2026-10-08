import styles from "./Account.module.css"
import { DropdownMenu, type MenuItem } from "@/components/ui/DropdownMenu"
import { useModalStore } from "@/store/modalStore"
import { HiOutlineUserCircle } from "react-icons/hi2"
import { MdOutlineLogout, MdOutlineSettings } from "react-icons/md"
import { SettingsModal } from "@/components/modals/SettingsModal"
import { AuthService } from "@/services/authService"
import { useUserStore } from "@/store/userStore"
import { useT } from "@/i18n"

export const Account = () => {
  const t = useT()
  const { openModal } = useModalStore()
  const username = useUserStore((s) => s.currentUser.username)
  const items: MenuItem[] = [
    {
      id: "settings",
      label: t("account.settings"),
      icon: <MdOutlineSettings />,
      onClick: () => openModal(<SettingsModal />)
    },
    {
      id: "logout",
      label: t("account.logout"),
      icon: <MdOutlineLogout />,
      onClick: () => AuthService.logout(),
      destructive: true
    }
  ]
  return (
    <div className={styles.account}>
      <span className={styles.username}>{username}</span>
      <DropdownMenu
        label={t("account.menu")}
        items={items}
        trigger={<HiOutlineUserCircle size={35} />}
        className={styles.menu}
      />
    </div>
  )
}
