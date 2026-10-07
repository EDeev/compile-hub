import { useState, useEffect } from "react"
import { Button } from "@/components/ui/Button"
import { Input } from "@/components/ui/Input"
import { PiNotePencil } from "react-icons/pi"
import styles from "./RenameModal.module.css"
import { useFileSystemStore } from "@/store/fileSystemStore"
import { validateFilename, validateFoldername } from "@/utils/validators"

interface RenameModalProps {
  type: "file" | "folder"
  initialName: string
  onConfirm: (newName: string) => void
  onCancel: () => void
}

export const RenameModal: React.FC<RenameModalProps> = ({
  type,
  initialName,
  onConfirm,
  onCancel
}) => {
  const { items } = useFileSystemStore()

  const [message, setMessage] = useState<{
    isValid: boolean
    text: string
  }>({ isValid: false, text: "" })

  const [displayValue, setDisplayValue] = useState("")
  const [extension, setExtension] = useState("")

  // разделение имени файла и расширения (ext) (для папок ext = "")
  useEffect(() => {
    const lastDotIndex = initialName.lastIndexOf(".")
    if (lastDotIndex > 0) {
      setExtension(initialName.substring(lastDotIndex))
      setDisplayValue(initialName.substring(0, lastDotIndex))
    } else {
      setExtension("")
      setDisplayValue(initialName)
    }
  }, [initialName])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newBaseName = e.target.value
    const newFullName = newBaseName + extension

    setDisplayValue(newBaseName)

    const validationResult =
      type === "file"
        ? validateFilename(newBaseName)
        : validateFoldername(newBaseName)

    const isAvailable = !items.some((item) => item.name === newFullName)

    if (!validationResult.isValid) {
      setMessage(validationResult)
      return
    }

    if (!isAvailable) {
      setMessage({
        isValid: false,
        text: ` A ${type} with this name already exists.`
      })
      return
    }

    setMessage(validationResult)
  }

  const handleConfirm = () => {
    if (message.isValid) {
      onConfirm(displayValue + extension)
    }
  }

  return (
    <div className={styles.content}>
      <p>
        Renaming {type} {initialName}
      </p>
      <div className={styles.inputContainer}>
        <Input
          autoFocus={true}
          placeholder='Enter new filename'
          icon={<PiNotePencil />}
          value={displayValue}
          message={message}
          onChange={handleChange}
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
          OK
        </Button>
        <Button variant='secondary' onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </div>
  )
}
