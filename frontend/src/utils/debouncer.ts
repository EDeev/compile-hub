export function createDebouncer(checkFunction: (username: string) => void, delay: number) {
  let timeoutId: ReturnType<typeof setTimeout> | null = null

  return {
    check: (username: string) => {
      if (timeoutId) clearTimeout(timeoutId)

      timeoutId = setTimeout(() => {
        checkFunction(username)
        timeoutId = null
      }, delay)
    },

    cancel: () => {
      if (timeoutId) {
        clearTimeout(timeoutId)
        timeoutId = null
      }
    }
  }
}
