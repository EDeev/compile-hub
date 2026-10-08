import { useModalStore } from "@/store/modalStore"
import styles from "./ItemInfoModal.module.css"
import { Button } from "@/components/ui/Button"
import { type Item } from "@/types"
import { timeAgo } from "@/utils/timeAgo"
import { languageByName } from "@/store/languagesStore"
import { useT } from "@/i18n"

interface FileInfoModalProps {
  item: Item
}

export const ItemInfoModal: React.FC<FileInfoModalProps> = ({ item }) => {
  const t = useT()
  const { closeModal } = useModalStore()
  const language = item.type === "file" ? languageByName(item.name)?.name : null

  return (
    <div className={styles.content}>
      <h2>{t("files.propertiesOf", { name: item.name })}</h2>
      <table>
        <tbody>
          <tr>
            <td className={styles.value}>{t("files.name")}:</td>
            <td>{item.name}</td>
          </tr>
          <tr>
            <td className={styles.value}>{t("files.type")}:</td>
            <td>
              {t(
                item.type === "file"
                  ? "files.creating.file"
                  : "files.creating.folder"
              ).replace(/^\S+\s/, "")}
            </td>
          </tr>
          {language && (
            <tr>
              <td className={styles.value}>{t("files.language")}:</td>
              <td>{language}</td>
            </tr>
          )}
          <tr>
            <td className={styles.value}>{t("files.size")}:</td>
            <td>{item.size}</td>
          </tr>
          {item.modified && (
            <tr>
              <td className={styles.value}>{t("files.modified")}:</td>
              <td>{timeAgo(item.modified)}</td>
            </tr>
          )}
        </tbody>
      </table>
      <Button variant='secondary' onClick={closeModal}>
        {t("common.close")}
      </Button>
    </div>
  )
}
