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

import { Icons, fileIcon } from "@/utils/icons"
import { useT } from "@/i18n"
import { useClickDragStore } from "@/store/clickDragStore"

export const Item: React.FC<ItemProps> = ({
  id,
  name,
  type,
  folder,
  language,
  size,
  modified,
  className = "",
  onClick,
  fileListRef,
  isSelected = false,
  isDragMode = false,
  canDropHere = false
}) => {
  const t = useT()
  const { handleRename, handleDelete, handleShowInfo, handleDownload } =
    useFileActions()

  const { selectForMove } = useClickDragStore()

  const [isMenuOpen, setIsMenuOpen] = useState(false)

  // Блокировка скролла при открытом меню
  useEffect(() => {
    const list = fileListRef?.current
    if (!list) return
    list.classList.toggle(styles.noScroll, isMenuOpen)
    return () => list.classList.remove(styles.noScroll)
  }, [isMenuOpen, fileListRef])

  const currentItem: FileSystemItem =
    type === "file"
      ? {
          id,
          name,
          size,
          modified,
          type: "file",
          folder: folder ?? null, // гарантируем, что folder точно есть
          language
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
        label: t("files.rename"),
        icon: <MdOutlineDriveFileRenameOutline />,
        onClick: () => handleRename(currentItem)
      }
    ]

    if (type === "file") {
      menuItems.push(
        {
          id: "move",
          label: t("files.move"),
          icon: <MdArrowForward />,
          onClick: () => {
            fileListRef?.current.scrollTo({ top: 0, behavior: "smooth" })
            selectForMove(currentItem)
          }
        },
        {
          id: "download",
          label: t("files.download"),
          icon: <MdDownload />,
          onClick: () =>
            currentItem.type === "file" && handleDownload(currentItem)
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
        label: t("files.delete"),
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
        label: t("files.properties"),
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

  return (
    <div className={itemClasses} onClick={() => onClick?.()}>
      <span className={styles.icon}>
        {type === "folder" ? (
          <img src={Icons.folderIcon} alt='' />
        ) : (
          fileIcon(name.split(".").reverse()[0].toLowerCase())
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
        <div className={styles.dropHint}>{t("files.moveHere")}</div>
      )}

      {!isDragMode && (
        <div onClick={(e: React.MouseEvent) => e.stopPropagation()}>
          <DropdownMenu
            label={t("files.actions", { name })}
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
