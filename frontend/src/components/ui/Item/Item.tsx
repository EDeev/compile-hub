import React, { useEffect, useState } from "react"
import {
  DropdownMenu,
  type MenuItem
} from "@/components/ui/DropdownMenu/DropdownMenu"
import { useFileActions } from "@/hooks/useFileActions"
import { type ItemProps, type Item as FileSystemItem } from "@/types/fileSystem" 
import styles from "./Item.module.css"
import { timeAgo } from "@/utils/timeAgo"
import {
  MdDownload,
  MdDeleteOutline,
  MdOutlineDriveFileRenameOutline,
  MdInfoOutline,
  MdArrowForward
} from "react-icons/md"

import { Icons } from "@/utils/icons"
import { useClickDragStore } from "@/store/clickDragStore"

export const Item: React.FC<ItemProps> = ({
  id,
  name,
  type,
  folder,
  size,
  modified,
  className = "",
  onClick,
  fileListRef,
  isSelected = false,
  isDragMode = false,
  canDropHere = false
}) => {
  const { handleRename, handleDelete, handleShowInfo } = useFileActions()

  const { selectForMove } = useClickDragStore()

  const [isMenuOpen, setIsMenuOpen] = useState(false)

  // Блокировка скролла при открытом меню
  useEffect(() => {
    if (!fileListRef?.current) return

    if (isMenuOpen) {
      fileListRef.current.classList.add(styles.noScroll)
    } else {
      fileListRef.current.classList.remove(styles.noScroll)
    }

    return () => {
      if (fileListRef?.current) {
        fileListRef.current.classList.remove(styles.noScroll)
      }
    }
  }, [isMenuOpen, fileListRef])

  const currentItem: FileSystemItem =
    type === "file"
      ? {
          id,
          name,
          size,
          modified,
          type: "file",
          folder: folder ?? null // гарантируем, что folder точно есть
        }
      : {
          id,
          name,
          size,
          modified,
          type: "folder"
        }

  const getMenuItems = (): MenuItem[] => {
    if (isDragMode) return []

    const menuItems: MenuItem[] = [
      {
        id: "rename",
        label: "Переименовать",
        icon: <MdOutlineDriveFileRenameOutline />,
        onClick: () => handleRename(currentItem)
      }
    ]

    if (type === "file") {
      menuItems.push(
        {
          id: "move",
          label: "Переместить",
          icon: <MdArrowForward />,
          onClick: () => {
            fileListRef?.current.scrollTo({ top: 0, behavior: "smooth" })
            selectForMove(currentItem)
          }
        },
        {
          id: "download",
          label: "Скачать",
          icon: <MdDownload />,
          onClick: () => console.log("тут будет загрузка")
        }
      )
    }

    menuItems.push(
      {
        id: "separator1",
        label: "",
        icon: "",
        separator: true,
        onClick: () => {}
      },
      {
        id: "delete",
        label: "Удалить",
        icon: <MdDeleteOutline />,
        onClick: () => handleDelete(currentItem),
        destructive: true
      },
      {
        id: "separator2",
        label: "",
        icon: "",
        separator: true,
        onClick: () => {}
      },
      {
        id: "info",
        label: "Свойства",
        icon: <MdInfoOutline />,
        onClick: () => handleShowInfo(currentItem)
      }
    )

    return menuItems
  }

  const itemClasses: string = [
    styles.fileItem,
    className,
    isSelected && styles.selected,
    isMenuOpen && styles.active,
    isDragMode && canDropHere && styles.dropTarget,
    isDragMode && !canDropHere && !isSelected && styles.disabled
  ]
    .filter(Boolean)
    .join(" ")

  const setFileIcon = (ext: string) => {
    switch (ext) {
      case "py":
        return <img src={Icons.pythonIcon} />
      case "go":
        return <img src={Icons.goIcon} />
      case "java":
        return <img src={Icons.javaIcon} />
      case "cpp":
        return <img src={Icons.cppIcon} />
      case "js":
        return <img src={Icons.jsIcon} />
    }
  }
  return (
    <div className={itemClasses} onClick={() => onClick?.()}>
      <span className={styles.icon}>
        {type === "folder" ? (
          <img src={Icons.folderIcon} />
        ) : (
          setFileIcon(name.split(".").reverse()[0])
        )}
      </span>

      <div className={styles.fileInfo}>
        <div className={styles.fileName}>{name}</div>
        {(size || modified) && (
          <div className={styles.additionalInfo}>
            {size && <span>{size}</span>}
            {size && modified && <span> • </span>}
            {modified && <span>{timeAgo(modified)}</span>}
          </div>
        )}
      </div>

      {isSelected && <div className={styles.selectedBadge}>✂️</div>}
      {isDragMode && canDropHere && (
        <div className={styles.dropHint}>Move here</div>
      )}

      {!isDragMode && (
        <div onClick={(e: React.MouseEvent) => e.stopPropagation()}>
          <DropdownMenu
            items={getMenuItems()}
            align='left'
            size='md'
            onOpenChange={setIsMenuOpen}
          />
        </div>
      )}
    </div>
  )
}
