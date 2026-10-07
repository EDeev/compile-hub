import styles from "./Account.module.css"
import { DropdownMenu, type MenuItem } from "@/components/ui/DropdownMenu"
import { useModalStore } from "@/store/modalStore"
import { HiOutlineUserCircle } from "react-icons/hi2"
import { MdOutlineLogout, MdOutlineSettings } from "react-icons/md"
import { SettingsModal } from "@/components/modals/SettingsModal"
import { AuthService } from "@/services/authService"

// MdInfoOutline иконка Info

export const Account = () => {
  const { openModal } = useModalStore()
  const items: MenuItem[] = [
    {
      id: "settings",
      label: "Settings",
      icon: <MdOutlineSettings />,
      onClick: () => openModal(<SettingsModal />)
    },
    {
      id: "Logout",
      label: "Log Out",
      icon: <MdOutlineLogout />,
      onClick: () => AuthService.logout(),
      destructive: true
    }
  ]
  return (
    <DropdownMenu
      items={items}
      trigger={<HiOutlineUserCircle size={35} />}
      className={styles.menu}
    />
  )
}
