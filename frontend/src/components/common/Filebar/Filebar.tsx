import { Button } from "@/components/ui/Button"
import { Input } from "@/components/ui/Input"
import styles from "./Filebar.module.css"
import { useClickDragStore } from "@/store/clickDragStore"
import { useFileNavigation } from "@/hooks/useFileNavigation"
import { MdSearch, MdChevronRight, MdChevronLeft } from "react-icons/md"
import { useEffect, useRef, useState, useMemo } from "react"
import { IoArrowBack } from "react-icons/io5"
import { Item } from "@/components/ui/Item"
import { useFileActions } from "@/hooks/useFileActions"
import {
  type ItemProps,
  type FolderItem,
  type FileItem
} from "@/types/fileSystem"
import { useFileFilter } from "@/hooks/useFileFilter"
import { useFileSystemStore } from "@/store/fileSystemStore"
import { useEditorState } from "@/store/editorStore"
import { CgSpinner } from "react-icons/cg"
import { useUserStore } from "@/store/userStore"

export const Filebar = () => {
  const [isFilebarOpen, setFilebarOpen] = useState(true)
  const [searchText, setSearchText] = useState("")
  const fileListRef = useRef<HTMLDivElement>(null!)

  // получение файлов отдельным хуком
  const { currentUser } = useUserStore()
  const { loadItems, items, isLoading } = useFileSystemStore()

  // отладка
  useEffect(
    () => console.log(`Текущий пользователь: ${currentUser.username}`),
    []
  )

  useEffect(() => {
    if (currentUser?.id && items.length === 0) {
      loadItems(currentUser.id) // Загружаем, если файлов нет
    }
  }, [currentUser?.id, loadItems, items.length])

  const folders = useMemo(
    () => items.filter((item): item is FolderItem => item.type === "folder"),
    [items]
  )

  // навигация отдельным хуком
  const {
    currentFolder,
    navigationHistory,
    goToFolder,
    goBack,
    getCurrentFolderName
  } = useFileNavigation(folders)

  const { setFile } = useEditorState()

  // пермещение файлов отдельным хуков
  const { isDragMode, cancelMove, isSelected, selectedItem } =
    useClickDragStore()

  const { handleCreate, handleMove } = useFileActions()

  // обработчик клика по папке
  const handleClick = (item: ItemProps) => {
    if (item.type === "folder") {
      isDragMode ? handleMove(selectedItem, item.id) : goToFolder(item.id)
    } else if (!isDragMode) {
      console.log("открытие файла")
      setFile(item as FileItem) // fix it
    }
  }

  const handleMoveToRoot = () => handleMove(selectedItem, null)

  const handleBackClick = () => {
    goBack()
    cancelMove()
  }

  const visibleItems = useFileFilter(items, currentFolder, searchText)

  return (
    <div
      className={`${styles.filebar} ${!isFilebarOpen ? styles.hiddenFilebar : ""}`}
    >
      <div className={styles.filebarContainer}>
        {/* Поиск */}
        <Input
          icon={<MdSearch />}
          placeholder='Searching files...'
          className={styles.search}
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
        />

        <hr />

        {/* Навигация */}
        <div className={styles.navigation}>
          {!isDragMode ? (
            <>
              <button
                onClick={handleBackClick}
                disabled={navigationHistory.length === 0}
                className={styles.backButton}
              >
                <IoArrowBack size={20} />
              </button>
              <span className={styles.currentPath}>
                {getCurrentFolderName()}
              </span>
            </>
          ) : (
            // кнопки в режиме перетаскивания
            <div className={styles.moveActionsButtons}>
              <button
                onClick={handleMoveToRoot}
                className={`${styles.moveToRootButton} ${styles.actionButton}`}
              >
                Move to home
              </button>
              <button
                onClick={cancelMove}
                className={`${styles.cancelButton} ${styles.actionButton}`}
              >
                Cancel
              </button>
            </div>
          )}
        </div>

        <hr />

        {/* Список файлов */}
        <div
          className={`${styles.fileList} ${isDragMode ? styles.dragMode : ""}`}
          ref={fileListRef}
        >
          {visibleItems.length > 0 ? (
            visibleItems.map((item: ItemProps) => (
              <Item
                key={item.id}
                {...item}
                onClick={
                  () => handleClick(item)
                  // тут же будет открытие файоа при item.type === "file"
                }
                fileListRef={fileListRef}
                isSelected={isSelected(item.id)}
                isDragMode={isDragMode}
                canDropHere={isDragMode && item.type === "folder"}
              />
            ))
          ) : (
            <span className={styles.searchError}>
              {currentUser.isGuest && items.length === 0
                ? "You can click the buttons below to create your first file or folder"
                : searchText
                  ? `File "${searchText}" not found`
                  : "This directory is empty"}
            </span>
          )}
        </div>

        <hr />

        {/* Кнопки создания папки или файла, папку в папке создавать нельзя*/}
        <div className={styles.createingButtons}>
          <Button
            variant='secondary'
            onClick={() => handleCreate("file", currentFolder)}
          >
            New file
          </Button>
          {currentFolder === null && (
            <Button variant='secondary' onClick={() => handleCreate("folder")}>
              New folder
            </Button>
          )}
        </div>
      </div>

      {/* Переключатель файлбара */}
      <button
        className={styles.openMenuButton}
        onClick={() => setFilebarOpen(!isFilebarOpen)}
      >
        {isFilebarOpen ? (
          <MdChevronLeft size={30} />
        ) : (
          <MdChevronRight size={30} />
        )}
      </button>
      {isLoading && <CgSpinner className={styles.loadSpinner} size={35} />}
    </div>
  )
}
