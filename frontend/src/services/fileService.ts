import { api } from "@/api/client"
import type { FileContent } from "@/api/types"
import { type FileItem, type FolderItem, type Item } from "@/types/fileSystem"

export interface ImportResult {
  items: Item[]
  skipped: number
}

export const FileService = {
  list: () => api<Item[]>("/files"),
  get: (id: number) => api<FileContent>(`/files/${id}`),
  createFile: (name: string, folderId: number | null, code?: string) =>
    api<FileItem>("/files", { method: "POST", body: { name, folderId, code } }),
  patchFile: (
    id: number,
    patch: { name?: string; folderId?: number | null; code?: string; stdin?: string }
  ) => api<FileItem>(`/files/${id}`, { method: "PATCH", body: patch }),
  deleteFile: (id: number) => api(`/files/${id}`, { method: "DELETE" }),
  createFolder: (name: string) => api<FolderItem>("/folders", { method: "POST", body: { name } }),
  renameFolder: (id: number, name: string) =>
    api<FolderItem>(`/folders/${id}`, { method: "PATCH", body: { name } }),
  deleteFolder: (id: number) => api(`/folders/${id}`, { method: "DELETE" }),
  importGuest: (body: {
    folders: { id: number; name: string }[]
    files: { name: string; folder: number | null; code: string; stdin: string }[]
  }) => api<ImportResult>("/files/import", { method: "POST", body })
}
