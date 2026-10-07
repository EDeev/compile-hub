import { type Item } from "@/types/fileSystem"

// export interface FileServiceInterface {
//   getItems(userId?: string): Promise<Item[]> | Item[]
//   saveItems?(items: Item[]): void
//   deleteItem?(id: number): Promise<void>
//   moveItem?(id: number, folderId: number | null): Promise<void>
//   checkLimits?(items: Item[], newItem: Item): boolean
// }

export const FileService = {
  async fetchUserFiles(userId: string): Promise<Item[]> {
    const response = await fetch(`http://95.31.185.229:9999/api/files?userId=${userId}`)
    if (!response.ok) {
      // тут сделать отображение ошибки
      throw new Error(`Failed to fetch files: ${response.status}`)
    }
    const data = await response.json()
    console.log(data)

    return data as Item[]
  },

  async deleteFileOnServer(id: number): Promise<void> {
    const response = await fetch(`/api/files/${id}`, {
      method: "DELETE"
    })
    if (!response.ok) {
      throw new Error(`Failed to delete file: ${response.status}`)
    }
  },

  async moveFileOnServer(id: number, folderId: number | null): Promise<void> {
    const response = await fetch(`/api/files/${id}/move`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ folderId })
    })
    if (!response.ok) {
      throw new Error(`Failed to move file: ${response.status}`)
    }
  }
}
