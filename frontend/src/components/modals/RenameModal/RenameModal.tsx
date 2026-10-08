import { useState } from "react"
import { Button } from "@/components/ui/Button"
import { Input } from "@/components/ui/Input"
import { PiNotePencil } from "react-icons/pi"
import styles from "./RenameModal.module.css"
import { useFileSystemStore } from "@/store/fileSystemStore"
import { validateFilename, validateFoldername } from "@/utils/validators"
import { useT } from "@/i18n"

interface RenameModalProps {
  type: "file" | "folder"
  initialName: string
  onConfirm: (newName: string) => void
  onCancel: () => void
}

const split = (name: string, type: "file" | "folder") => {
  const dot = name.lastIndexOf(".")
  return type === "file" && dot > 0
    ? [name.slice(0, dot), name.slice(dot)]
    : [name, ""]
}

export const RenameModal: React.FC<RenameModalProps> = ({
  type,
  initialName,
  onConfirm,
  onCancel
}) => {
  const t = useT()
  const { items } = useFileSystemStore()
  const [base, extension] = split(initialName, type)
  const [displayValue, setDisplayValue] = useState(base)
  const [message, setMessage] = useState({ isValid: false, text: "" })
  const current = items.find((i) => i.name === initialName && i.type === type)
  const folder = current?.type === "file" ? current.folder : null

  const handleChange = (value: string) => {
    setDisplayValue(value)
    const result =
      type === "file" ? validateFilename(value) : validateFoldername(value)
    const fullName = type === "file" ? value + extension : value.trim()
    const taken = items.some(
      (i) =>
        i !== current &&
        i.type === type &&
        i.name === fullName &&
        (type === "folder" || (i.type === "file" && i.folder === folder))
    )
    setMessage(
      result.isValid && taken
        ? { isValid: false, text: t("validation.nameTaken") }
        : result
    )
  }

  const handleConfirm = () => {
    if (message.isValid)
      onConfirm(
        type === "file" ? displayValue + extension : displayValue.trim()
      )
  }

  return (
    <div className={styles.content}>
      <p>{t("files.renaming", { name: initialName })}</p>
      <div className={styles.inputContainer}>
        <Input
          autoFocus={true}
          placeholder={t("files.newName")}
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
          <span className={styles.extension}>{extension}</span>
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
