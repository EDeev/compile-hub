  export interface BaseItem {
    id: number
    name: string
    size?: string
    modified?: string
  }

export interface FileItem extends BaseItem {
  type: "file"
  folder: number | null
}

export interface FolderItem extends BaseItem {
  type: "folder"
}

export type Item = FileItem | FolderItem

export interface ItemProps {
  id: number
  name: string
  type: "file" | "folder"
  folder?: number | null
  size?: string
  modified?: string
  className?: string
  fileListRef?: React.RefObject<HTMLDivElement>
  onClick?: () => void

  // Drag & drop props
  isSelected?: boolean
  isDragMode?: boolean
  canDropHere?: boolean
}
