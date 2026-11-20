import { Button } from "@/components/ui/Button"
import { Input } from "@/components/ui/Input"
import styles from "./Filebar.module.css"
import { useClickDragStore } from "@/store/clickDragStore"
import { useFileNavigation } from "@/hooks/useFileNavigation"
import { MdSearch, MdChevronRight, MdChevronLeft } from "react-icons/md"
import { useRef, useState, useMemo } from "react"
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
import { useT } from "@/i18n"
import { useIsMobile } from "@/hooks/useIsMobile"
import { useUiStore } from "@/store/uiStore"

export const Filebar = () => {
  const [isFilebarOpen, setFilebarOpen] = useState(true)
  const [searchText, setSearchText] = useState("")
  const fileListRef = useRef<HTMLDivElement>(null!)

  const t = useT()
  // на телефоне — выдвижная панель поверх редактора, открывается кнопкой в шапке
  const isMobile = useIsMobile()
  const { filesOpen, setFilesOpen } = useUiStore()
  // файлы грузит AuthService при входе и восстановлении сессии, у гостя — localStorage
  const { items, isLoading } = useFileSystemStore()

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

  const { openFile } = useEditorState()

  // пермещение файлов отдельным хуков
  const { isDragMode, cancelMove, isSelected, selectedItem } =
    useClickDragStore()

  const { handleCreate, handleMove } = useFileActions()

  // обработчик клика по папке
  const handleClick = (item: ItemProps) => {
    if (item.type === "folder") {
      if (isDragMode) handleMove(selectedItem, item.id)
      else goToFolder(item.id)
    } else if (!isDragMode) {
      openFile(item as FileItem)
      setFilesOpen(false)
    }
  }

  const handleMoveToRoot = () => handleMove(selectedItem, null)

  const handleBackClick = () => {
    goBack()
    cancelMove()
  }

  const visibleItems = useFileFilter(items, currentFolder, searchText)
  const panelHidden = isMobile ? !filesOpen : !isFilebarOpen

  const classes = [
    styles.filebar,
    isMobile ? styles.mobile : !isFilebarOpen && styles.hiddenFilebar,
    isMobile && filesOpen && styles.mobileOpen
  ]
    .filter(Boolean)
    .join(" ")

  return (
    <>
      {isMobile && filesOpen && (
        <div className={styles.backdrop} onClick={() => setFilesOpen(false)} />
      )}
      <div className={classes}>
        {/* Переключатель файлбара (на телефоне — кнопка в шапке). Первым в разметке и вверху панели: Tab идёт
            сверху вниз — переключатель, поиск, список, кнопки создания */}
        {!isMobile && (
          <button
            className={styles.openMenuButton}
            aria-label={t(isFilebarOpen ? "files.hide" : "files.show")}
            onClick={() => setFilebarOpen(!isFilebarOpen)}
          >
            {isFilebarOpen ? (
              <MdChevronLeft size={30} />
            ) : (
              <MdChevronRight size={30} />
            )}
          </button>
        )}
        {/* закрытая панель уезжает за край экрана — inert убирает её из обхода Tab и для экранных читалок */}
        <div className={styles.filebarContainer} inert={panelHidden}>
          {/* Поиск */}
          <Input
            icon={<MdSearch />}
            placeholder={t("files.search")}
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
                  aria-label={t("files.back")}
                >
                  <IoArrowBack size={20} />
                </button>
                <span className={styles.currentPath}>
                  {getCurrentFolderName() ?? t("files.home")}
                </span>
              </>
            ) : (
              // кнопки в режиме перетаскивания
              <div className={styles.moveActionsButtons}>
                <button
                  onClick={handleMoveToRoot}
                  className={`${styles.moveToRootButton} ${styles.actionButton}`}
                >
                  {t("files.moveHome")}
                </button>
                <button
                  onClick={cancelMove}
                  className={`${styles.cancelButton} ${styles.actionButton}`}
                >
                  {t("files.cancel")}
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
                {items.length === 0
                  ? t("files.firstHint")
                  : searchText
                    ? t("files.notFound", { name: searchText })
                    : t("files.empty")}
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
              {t("files.newFile")}
            </Button>
            {currentFolder === null && (
              <Button
                variant='secondary'
                onClick={() => handleCreate("folder")}
              >
                {t("files.newFolder")}
              </Button>
            )}
          </div>
        </div>

        {isLoading && <CgSpinner className={styles.loadSpinner} size={35} />}
      </div>
    </>
  )
}
