import { useState } from "react"
import { type FolderItem } from "@/types/fileSystem"

export const useFileNavigation = (folders: FolderItem[]) => {
  const [currentFolder, setCurrentFolder] = useState<number | null>(null)
  const [navigationHistory, setNavigationHistory] = useState<(number | null)[]>([])

  const goToFolder = (folderId: number) => {
    setNavigationHistory((prev) => [...prev, currentFolder])
    setCurrentFolder(folderId)
  }

  const goBack = () => {
    if (navigationHistory.length === 0) return

    const previousFolder = navigationHistory[navigationHistory.length - 1]
    setCurrentFolder(previousFolder)
    setNavigationHistory((prev) => prev.slice(0, -1))
  }

  const getCurrentFolderName = () => {
    if (currentFolder === null) return "Home"
    return folders.find((f) => f.id === currentFolder)?.name || "Unknown folder"
  }

  return {
    currentFolder,
    navigationHistory,
    goToFolder,
    goBack,
    getCurrentFolderName
  }
}
