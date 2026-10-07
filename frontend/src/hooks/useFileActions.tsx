import { useCallback } from "react"
import { useModalStore } from "@/store/modalStore"
import { useFileSystemStore } from "@/store/fileSystemStore"
import { RenameModal } from "@/components/modals/RenameModal"
import { ConfirmModal } from "@/components/modals/ConfirmModal"
import { CreateItemModal } from "@/components/modals/CreateItemModal"
import { ItemInfoModal } from "@/components/modals/ItemInfoModal"
import { useClickDragStore } from "@/store/clickDragStore"
import { type FileItem, type Item } from "@/types/fileSystem"
import { useEditorState } from "@/store/editorStore"

// show notification на будущий попап внизу справа
export const useFileActions = () => {
  const { selectForMove, cancelMove } = useClickDragStore()
  const { openModal, closeModal } = useModalStore()
  const { setFile } = useEditorState()
  const { items, addItem, updateItem, deleteItem, moveItem } =
    useFileSystemStore()

  const handleRename = useCallback(
    async (item: Item) => {
      try {
        const newName = await new Promise<string | null>((resolve) => {
          openModal(
            <RenameModal
              type={item.type}
              initialName={item.name}
              onCancel={closeModal}
              onConfirm={(newName: string) => {
                resolve(newName)
                closeModal()
              }}
            />
          )
        })

        if (newName && newName !== item.name) {
          // Оптимистичное обновление интерфейса
          updateItem(item.id, { name: newName })

          // Запрос к серверу (заглушка)
          // await FileService.renameFileOnServer(item.id, newName);

          // тут показ уведомления можно
        }
      } catch (error) {
        console.error("Ошибка переименования:", error)
        // тут показ уведомления можно
      }
    },
    [openModal, closeModal, updateItem]
  )

  const handleDelete = useCallback(
    async (item: Item) => {
      let confirmed = false
      try {
        confirmed = await new Promise<boolean>((resolve) => {
          openModal(
            <ConfirmModal
              type='warning'
              title='Are you sure?'
              message="You won't be able to restore this file"
              onConfirm={() => resolve(true)}
              onCancel={() => resolve(false)}
            />
          )
        })
      } finally {
        closeModal()
      }

      if (!confirmed) {
        return
      }

      try {
        // Оптимистичное удаление
        deleteItem(item.id)

        // тут показ уведомления можно
      } catch (error) {
        console.error("Ошибка удаления:", error)
        // тут показ уведомления можно
      }
    },
    [deleteItem]
  )

  const handleMove = useCallback(
    async (item: Item | null, targetFolderId: number | null) => {
      if (item && item.type === "file") {
        console.log("kek")
        // После выбора папки для перемещения (например, через модальное окно или drag-and-drop)
        // вызываем:
        // await FileService.moveFileOnServer(item.id, targetFolderId);
        moveItem(item.id, targetFolderId)
        cancelMove()
      }
    },
    [selectForMove]
  )

  const handleShowInfo = useCallback((item: Item) => {
    openModal(<ItemInfoModal item={item} />)
  }, [])

  const handleCreate = useCallback(
    async (type: "file" | "folder", parentFolderId: number | null = null) => {
      const name = await new Promise<string | null>((resolve) => {
        openModal(
          <CreateItemModal
            type={type}
            onCancel={closeModal}
            onConfirm={(name: string) => {
              resolve(name)
              closeModal()
            }}
          />
        )
      })

      if (name) {
        const lastId = items[items.length - 1]?.id ?? 0
        let newItem

        if (type === "file") {
          newItem = {
            id: lastId + 1,
            name: name,
            type: type,
            folder: parentFolderId,
            size: "0b",
            modified: new Date().toISOString()
          }
        } else {
          newItem = {
            id: lastId + 1,
            name: name,
            type: type,
            size: "0b",
            modified: new Date().toISOString()
          }
        }

        addItem(newItem)

        if (type === "file") {
          setFile(newItem as FileItem)
        }
      }
    },
    [items, addItem, openModal, closeModal]
  )

  return {
    handleRename,
    handleDelete,
    handleMove,
    handleShowInfo,
    handleCreate
  }
}
