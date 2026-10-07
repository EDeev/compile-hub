export const VALIDATION_RULES = {
  USERNAME: {
    MIN_LENGTH: 3,
    MAX_LENGTH: 20,
    PATTERN: /^[a-zA-Z0-9_]+$/
  },
  PASSWORD: {
    MIN_LENGTH: 8,
    MAX_LENGTH: 32,
    PATTERNS: {
      LATIN_ONLY: /^[A-Za-z0-9!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]*$/,
      UPPERCASE: /[A-Z]/,
      LOWERCASE: /[a-z]/,
      NUMBER: /[0-9]/
    }
  },
  EMAIL: {
    PATTERN: /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  },
  FILENAME: {
    MAX_LENGTH: 20,
    PATTERN: /^[a-zA-Z0-9_-]*$/
  },
  FOLDERNAME: {
    MAX_LENGTH: 20,
    PATTERN: /^[\p{L}\d_ -]+$/u
  },
  TIMING: {
    DEBOUNCE_DELAY: 300,
    SERVER_TIMEOUT: 5000 // максимальное время ожидания от сервер
  }
} as const

export const GUEST_LIMITS = {
  MAX_FILES: 10,
  MAX_FOLDERS: 3
}

// export const APP_SETTINGS = {
//   : "Python"
// }
