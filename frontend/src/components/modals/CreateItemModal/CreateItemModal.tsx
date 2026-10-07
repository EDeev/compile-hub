import { useState, useRef } from "react"
import { Button } from "@/components/ui/Button"
import { Input } from "@/components/ui/Input"
import { PiNotePencil } from "react-icons/pi"
import styles from "./CreateItemModal.module.css"
import { useFileSystemStore } from "@/store/fileSystemStore"
import { validateFilename, validateFoldername } from "@/utils/validators"

interface CreateItemModalProps {
  type: "file" | "folder"
  onConfirm: (name: string) => void
  onCancel: () => void
}

export const CreateItemModal: React.FC<CreateItemModalProps> = ({
  type,
  onConfirm,
  onCancel
}) => {
  const { items } = useFileSystemStore()

  const [message, setMessage] = useState<{
    isValid: boolean
    text: string
  }>({ isValid: false, text: "" })

  // для папок расширение (ext) всегда = ""
  const defaultExtension = type === "file" ? ".py" : ""

  const [displayValue, setDisplayValue] = useState("")
  const [extension, setExtension] = useState(defaultExtension)
  const inputRef = useRef<HTMLInputElement>(null)

  // разделение имени файла и расширения (ext) (для папок ext = "")

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const name = e.target.value
    const fullName = e.target.value + extension

    setDisplayValue(name)

    const validationResult =
      type === "file" ? validateFilename(name) : validateFoldername(name)

    const isAvailable = !items.some((item) => item.name === fullName)

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
    // для файла добавляем расширение
    if (message.isValid) {
      onConfirm(displayValue + extension)
    }
  }

  return (
    <div className={styles.content}>
      <p>Creating {type}</p>
      <div className={styles.inputContainer}>
        <Input
          autoFocus={true}
          autoComplete='off'
          name='file-name'
          ref={inputRef}
          placeholder={`Enter ${type}name ${type === "file" ? "without extension" : ""}`}
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
          <select
            className={styles.selectExt}
            onChange={(e) => setExtension(e.target.value)}
            value={extension}
          >
            <option value='.py'>Python</option>
            <option value='.go'>Golang</option>
            <option value='.java'>Java</option>
            <option value='.cpp'>C++</option>
            <option value='.js'>JavaScript</option>
          </select>
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
