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
import { t } from "@/i18n"

export const useFileActions = () => {
  const { cancelMove } = useClickDragStore()
  const { openModal, closeModal } = useModalStore()
  const { rename, remove, move, createFile, createFolder, getContent } =
    useFileSystemStore()

  const askName = useCallback(
    (render: (resolve: (name: string | null) => void) => React.ReactElement) =>
      new Promise<string | null>((resolve) => openModal(render(resolve))),
    [openModal]
  )

  const handleRename = useCallback(
    async (item: Item) => {
      const newName = await askName((resolve) => (
        <RenameModal
          type={item.type}
          initialName={item.name}
          onCancel={() => {
            resolve(null)
            closeModal()
          }}
          onConfirm={(name: string) => {
            resolve(name)
            closeModal()
          }}
        />
      ))
      if (!newName || newName === item.name) return
      if (await rename(item, newName)) {
        const editor = useEditorState.getState()
        if (item.type === "file" && editor.currentFile?.id === item.id) {
          useEditorState.setState({
            currentFile: { ...editor.currentFile, name: newName }
          })
        }
      }
    },
    [askName, closeModal, rename]
  )

  const handleDelete = useCallback(
    async (item: Item) => {
      const confirmed = await new Promise<boolean>((resolve) => {
        openModal(
          <ConfirmModal
            type='warning'
            title={t("files.deleteTitle")}
            message={t(
              item.type === "file" ? "files.deleteFile" : "files.deleteFolder",
              { name: item.name }
            )}
            onConfirm={() => resolve(true)}
            onCancel={() => {
              resolve(false)
              closeModal()
            }}
          />
        )
      })
      if (!confirmed) return
      const editor = useEditorState.getState()
      const openFile = editor.currentFile
      if (await remove(item)) {
        const closesEditor =
          openFile &&
          (item.type === "file"
            ? openFile.id === item.id
            : openFile.folder === item.id)
        if (closesEditor) editor.closeFile()
      }
    },
    [openModal, closeModal, remove]
  )

  const handleMove = useCallback(
    async (item: Item | null, targetFolderId: number | null) => {
      if (item && item.type === "file" && item.folder !== targetFolderId) {
        await move(item, targetFolderId)
      }
      cancelMove()
    },
    [move, cancelMove]
  )

  const handleShowInfo = useCallback(
    (item: Item) => {
      openModal(<ItemInfoModal item={item} />)
    },
    [openModal]
  )

  const handleDownload = useCallback(
    async (item: FileItem) => {
      const content = await getContent(item)
      if (!content) return
      const url = URL.createObjectURL(
        new Blob([content.code], { type: "text/plain;charset=utf-8" })
      )
      const link = document.createElement("a")
      link.href = url
      link.download = item.name
      link.click()
      URL.revokeObjectURL(url)
    },
    [getContent]
  )

  const handleCreate = useCallback(
    async (type: "file" | "folder", parentFolderId: number | null = null) => {
      const name = await askName((resolve) => (
        <CreateItemModal
          type={type}
          folderId={parentFolderId}
          onCancel={() => {
            resolve(null)
            closeModal()
          }}
          onConfirm={(value: string) => {
            resolve(value)
            closeModal()
          }}
        />
      ))
      if (!name) return
      if (type === "file") {
        const file = await createFile(name, parentFolderId)
        if (file) await useEditorState.getState().openFile(file)
      } else {
        await createFolder(name)
      }
    },
    [askName, closeModal, createFile, createFolder]
  )

  return {
    handleRename,
    handleDelete,
    handleMove,
    handleShowInfo,
    handleDownload,
    handleCreate
  }
}
