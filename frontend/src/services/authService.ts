import { useFileSystemStore } from "@/store/fileSystemStore"
import { useUserStore } from "@/store/userStore"
import { type User, type Item } from "@/types"

export const AuthService = {
  async login(userData: { username: string; password: string }) {
    try {
      const response = await fetch("http://95.31.185.229:9999/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(userData)
      })

      if (!response.ok) {
        if (response.status == 401) {
          return ["Failed to log in, check your credentials", false] as [string, boolean]
        } else {
          return ["Failed to log in, please try again", false] as [string, boolean]
        }
      }

      const data = await response.json()

      const isCorrect =
        "id" in data &&
        "email" in data &&
        "isGuest" in data &&
        "username" in data &&
        "token" in data

      if (!isCorrect) {
        return ["HTTP error, plase try again later", false] as [string, boolean]
      }
      // установка залогиневшегося юзера как currentUser в userStore
      useUserStore.getState().login({
        email: data.email,
        id: data.id,
        isGuest: data.isGuest,
        username: data.username,
        token: data.token
      })

      // await useFileSystemStore.getState().loadItems(testUser.id)

      return ["You successfully logged in", true] as [string, boolean]
    } catch (error) {
      console.error("Login error:", error)
      return ["Failed to log in, check your credentials", false] as [string, boolean]
    }
  },

  async logout() {
    // Опционально: можно сделать запрос к API для logout
    useUserStore.getState().logout()
  },

  async register(userData: { email: string; username: string; password: string }) {
    const { currentUser } = useUserStore.getState() // для миграции файлов
    const guestFiles = currentUser.isGuest ? useFileSystemStore.getState().items : []

    const response = await fetch("http://95.31.185.229:9999/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(userData)
    })

    if (!response.ok) {
      return ["Failed to sign up, please try again", false] as [string, boolean]
    }

    const data = await response.json()

    if (data.success) {
      return ["Succesully signed up, please login", true] as [string, boolean]
    } else {
      return ["Failed to signed up, try later", false] as [string, boolean]
    }

    // МИГРАЦИЯ ФАЙЛОВ ПОЗЖЕ

    // if (currentUser.isGuest && guestFiles.length > 0) {
    //   await this.migrateFiles(guestFiles, user.id)
    // }
  }

  // async migrateFiles(files: Item[], userId: string) {
  //   try {
  //     // Оптимизация: переносим только последние 20 файлов
  //     const filesToMigrate = files.slice(-20).filter((f) => f.size < 500_000) // 500KB max

  //     await fetch("/api/files/migrate", {
  //       method: "POST",
  //       body: JSON.stringify({
  //         userId,
  //         files: filesToMigrate
  //       })
  //     })

  //     // Очистка гостевых данных
  //     localStorage.removeItem("guest_files")
  //   } catch (error) {
  //     console.error("Migration failed", error)
  //     // Файлы остаются в гостевом хранилище
  //   }
  // }
}
