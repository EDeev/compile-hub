import { useMemo } from "react"
import { type Item } from "@/types/fileSystem"

export const useFileFilter = (
  items: Item[],
  currentFolder: number | null,
  searchText: string
): Item[] => {
  return useMemo(() => {
    let filteredItems: Item[]

    if (currentFolder === null) {
      // в корне показываем папки и файлы
      filteredItems = items.filter(
        (item) => item.type === "folder" || (item.type === "file" && item.folder === null)
      )
    } else {
      // в папке:  файлы, у которых совпадает свойство folder
      filteredItems = items.filter((item) => item.type === "file" && item.folder === currentFolder)
    }

    // фильтрация (поиск) по имени
    if (searchText.trim()) {
      const lowerSearch = searchText.toLowerCase()
      filteredItems = filteredItems.filter((item) => item.name.toLowerCase().includes(lowerSearch))
    }

    // сортировка если находимся в корне сначала папки, потом файлы
    return filteredItems.sort((a, b) => {
      if (a.type === "folder" && b.type !== "folder") return -1
      if (a.type !== "folder" && b.type === "folder") return 1

      const dateA = new Date(a.modified ?? 0)
      const dateB = new Date(b.modified ?? 0)

      return dateB.getTime() - dateA.getTime()
    })
  }, [items, currentFolder, searchText])
}
