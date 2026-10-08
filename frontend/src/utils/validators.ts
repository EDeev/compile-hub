import { VALIDATION_RULES } from "./constants"
import { t } from "@/i18n"

type ValidationResult = {
  isValid: boolean
  text: string
}

const ok: ValidationResult = { isValid: true, text: "" }
const bad = (text: string): ValidationResult => ({ isValid: false, text })

export const FormValidators = {
  validateUsername(username: string): ValidationResult {
    const { MIN_LENGTH: min, MAX_LENGTH: max, PATTERN } = VALIDATION_RULES.USERNAME
    if (!username) return bad(t("validation.usernameRequired"))
    if (username.length < min || username.length > max)
      return bad(t("validation.usernameLength", { min, max }))
    if (!PATTERN.test(username)) return bad(t("validation.usernameChars"))
    return ok
  },

  validateEmail(email: string): ValidationResult {
    if (!email) return bad(t("validation.emailRequired"))
    if (!VALIDATION_RULES.EMAIL.PATTERN.test(email)) return bad(t("validation.emailFormat"))
    return ok
  },

  validatePassword(password: string): ValidationResult {
    const { MIN_LENGTH: min, MAX_LENGTH: max, PATTERNS } = VALIDATION_RULES.PASSWORD
    if (!password) return bad(t("validation.passwordRequired"))
    if (password.length < min || password.length > max)
      return bad(t("validation.passwordLength", { min, max }))
    if (!PATTERNS.LATIN_ONLY.test(password)) return bad(t("validation.passwordLatin"))
    if (!PATTERNS.UPPERCASE.test(password)) return bad(t("validation.passwordUpper"))
    if (!PATTERNS.LOWERCASE.test(password)) return bad(t("validation.passwordLower"))
    if (!PATTERNS.NUMBER.test(password)) return bad(t("validation.passwordDigit"))
    return ok
  }
}

export const validateFilename = (name: string): ValidationResult => {
  const { MAX_LENGTH, PATTERN } = VALIDATION_RULES.FILENAME
  if (name.length === 0) return bad(t("validation.nameEmpty"))
  if (!PATTERN.test(name)) return bad(t("validation.fileChars"))
  if (name.length > MAX_LENGTH) return bad(t("validation.nameLength", { max: MAX_LENGTH }))
  return ok
}

export const validateFoldername = (name: string): ValidationResult => {
  const { MAX_LENGTH, PATTERN } = VALIDATION_RULES.FOLDERNAME
  if (name.trim().length === 0) return bad(t("validation.nameEmpty"))
  if (!PATTERN.test(name)) return bad(t("validation.folderChars"))
  if (name.length > MAX_LENGTH) return bad(t("validation.nameLength", { max: MAX_LENGTH }))
  return ok
}
