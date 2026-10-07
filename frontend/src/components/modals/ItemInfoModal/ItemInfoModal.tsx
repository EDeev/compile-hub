import { useModalStore } from "@/store/modalStore"
import styles from "./ItemInfoModal.module.css"
import { Button } from "@/components/ui/Button"
import { type Item } from "@/types"
import { timeAgo } from "@/utils/timeAgo"

interface FileInfoModalProps {
  item: Item
}

export const ItemInfoModal: React.FC<FileInfoModalProps> = ({ item }) => {
  const { closeModal } = useModalStore()

  return (
    <div className={styles.content}>
      <h2>
        Properties of {item.type} {item.name}
      </h2>
      <table>
        <tbody>
          <tr>
            <td className={styles.value}>Name:</td>
            <td>{item.name}</td>
          </tr>
          <tr>
            <td className={styles.value}>Type:</td>
            <td>{item.type}</td>
          </tr>
          <tr>
            <td className={styles.value}>Size:</td>
            <td>{item.size}</td>
          </tr>
          {item.modified && (
            <tr>
              <td className={styles.value}>Last modified:</td>
              <td>{timeAgo(item.modified)}</td>
            </tr>
          )}
        </tbody>
      </table>
      <Button variant='secondary' onClick={closeModal}>
        Close
      </Button>
    </div>
  )
}
