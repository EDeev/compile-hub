import { useState } from "react"
import { Button } from "@/components/ui/Button"
import { Input } from "@/components/ui/Input"
import { PiNotePencil } from "react-icons/pi"
import styles from "./CreateItemModal.module.css"
import { useFileSystemStore } from "@/store/fileSystemStore"
import { useLanguagesStore } from "@/store/languagesStore"
import { validateFilename, validateFoldername } from "@/utils/validators"
import { useT } from "@/i18n"

interface CreateItemModalProps {
  type: "file" | "folder"
  folderId?: number | null
  onConfirm: (name: string) => void
  onCancel: () => void
}

export const CreateItemModal: React.FC<CreateItemModalProps> = ({
  type,
  folderId = null,
  onConfirm,
  onCancel
}) => {
  const t = useT()
  const { items } = useFileSystemStore()
  const languages = useLanguagesStore((s) => s.languages)
  const [message, setMessage] = useState({ isValid: false, text: "" })
  const [displayValue, setDisplayValue] = useState("")
  // для папки расширения нет
  const [extension, setExtension] = useState(
    type === "file" ? `.${languages[0]?.extensions[0] ?? "py"}` : ""
  )

  const validate = (name: string, ext: string) => {
    const result =
      type === "file" ? validateFilename(name) : validateFoldername(name)
    if (!result.isValid) return result
    const fullName = type === "file" ? name + ext : name.trim()
    // имена уникальны в пределах папки (у папок — среди папок)
    const taken = items.some((item) =>
      type === "file"
        ? item.type === "file" &&
          item.folder === folderId &&
          item.name === fullName
        : item.type === "folder" && item.name === fullName
    )
    return taken ? { isValid: false, text: t("validation.nameTaken") } : result
  }

  const handleChange = (name: string) => {
    setDisplayValue(name)
    setMessage(validate(name, extension))
  }

  const handleConfirm = () => {
    if (message.isValid)
      onConfirm(
        type === "file" ? displayValue + extension : displayValue.trim()
      )
  }

  return (
    <div className={styles.content}>
      <p>
        {t(type === "file" ? "files.creating.file" : "files.creating.folder")}
      </p>
      <div className={styles.inputContainer}>
        <Input
          autoFocus={true}
          autoComplete='off'
          name='file-name'
          placeholder={t(
            type === "file"
              ? "files.namePlaceholder.file"
              : "files.namePlaceholder.folder"
          )}
          icon={<PiNotePencil />}
          value={displayValue}
          message={message}
          onChange={(e) => handleChange(e.target.value)}
          className={styles.input}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleConfirm()
          }}
        />
        {type === "file" && (
          <select
            className={styles.selectExt}
            onChange={(e) => {
              setExtension(e.target.value)
              setMessage(validate(displayValue, e.target.value))
            }}
            value={extension}
          >
            {languages.map((lang) => (
              <option key={lang.id} value={`.${lang.extensions[0]}`}>
                {lang.name}
              </option>
            ))}
          </select>
        )}
      </div>
      <div className={styles.buttonGroup}>
        <Button
          variant='primary'
          disabled={!message.isValid}
          onClick={handleConfirm}
        >
          {t("common.ok")}
        </Button>
        <Button variant='secondary' onClick={onCancel}>
          {t("common.cancel")}
        </Button>
      </div>
    </div>
  )
}
