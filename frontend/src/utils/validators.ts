import { VALIDATION_RULES } from "./constants"

type ValidationResult = {
  isValid: boolean
  text: string
}

export const FormValidators = {
  /* prettier-ignore */
  validateUsername(username: string): ValidationResult {

    const minLength = VALIDATION_RULES.USERNAME.MIN_LENGTH
    const maxLength = VALIDATION_RULES.USERNAME.MAX_LENGTH
    const pattern = VALIDATION_RULES.USERNAME.PATTERN

    if (!username) return { isValid: false, text: "Username is required" }

    if (username.length < minLength) return { isValid: false, text: `Username must be at least ${minLength} characters` }

    if (username.length > maxLength) return { isValid: false, text: `Username must be less than ${maxLength} characters` }

    if (!pattern.test(username)) return { isValid: false, text: "Username can only contain latin letters, numbers, and underscores" }

    return { isValid: true, text: "" }
  },

  validateEmail(email: string): ValidationResult {
    const pattern = VALIDATION_RULES.EMAIL.PATTERN

    if (!email) return { isValid: false, text: "Email is required" }

    if (!pattern.test(email)) return { isValid: false, text: "Invalid email format" }

    return { isValid: true, text: "" }
  },

  /* prettier-ignore */
  validatePassword(password: string): ValidationResult {
    
    const minLength = VALIDATION_RULES.PASSWORD.MIN_LENGTH
    const maxLength = VALIDATION_RULES.PASSWORD.MAX_LENGTH
    const patterns = VALIDATION_RULES.PASSWORD.PATTERNS

    if (!password) return { isValid: false, text: "Password is required" }

    if (password.length < minLength) return { isValid: false, text: `Password must be at least ${minLength} characters` }

    if (password.length > maxLength) return { isValid: false, text: `Password must be less than ${maxLength} characters` }

    if (!patterns.LATIN_ONLY.test(password)) return { isValid: false, text: "Password must contain latin only symbols" }

    if (!patterns.UPPERCASE.test(password)) return { isValid: false, text: "Password must contain at least one latin uppercase letter" }

    if (!patterns.LOWERCASE.test(password)) return { isValid: false, text: "Password must contain at least one latin lowercase letter" }

    if (!patterns.NUMBER.test(password)) return { isValid: false, text: "Password must contain at least one number" }

    return { isValid: true, text: "" }
  }
}

export const validateFilename = (name: string) => {
  const isValid = VALIDATION_RULES.FILENAME.PATTERN.test(name)
  const hasCorrectLen = name.length <= VALIDATION_RULES.FILENAME.MAX_LENGTH

  if (!isValid) {
    return {
      isValid: false,
      text: "Only latin letters, numbers, underscores and hyphens allowed"
    }
  }
  if (!hasCorrectLen) {
    return {
      isValid: false,
      text: `Filename must be less than ${VALIDATION_RULES.FILENAME.MAX_LENGTH} characters`
    }
  }
  if (name.length === 0) {
    return { isValid: false, text: "File name cannot be empty" }
  }

  return { isValid: true, text: "" }
}

export const validateFoldername = (name: string) => {
  const isValid = VALIDATION_RULES.FOLDERNAME.PATTERN.test(name)
  const hasCorrectLen = name.length <= VALIDATION_RULES.FILENAME.MAX_LENGTH

  if (!isValid) {
    return {
      isValid: false,
      text: "Only letters, numbers, underscores and hyphens allowed"
    }
  }
  if (!hasCorrectLen) {
    return {
      isValid: false,
      text: `Filename must be less than ${VALIDATION_RULES.FILENAME.MAX_LENGTH} characters`
    }
  }
  if (name.length === 0) {
    return { isValid: false, text: "File name cannot be empty" }
  }

  return { isValid: true, text: "" }
}
