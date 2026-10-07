import { Input } from "@/components/ui/Input"
import { Button } from "@/components/ui/Button"
import { Switcher } from "@/components/ui/Switcher"
import { useEditorSettings } from "@/store/editorStore"
import styles from "./EditorTab.module.css"

export const EditorTab = () => {
  const MIN_FONT_SIZE = 12
  const MAX_FONT_SIZE = 24

  const { fontSize, changeFontSize, autocomplete, switchAutocomplete } =
    useEditorSettings()

  return (
    <div className={styles.mainContainer}>
      <h3>Editor settings</h3>
      <div className={styles.optionContainer}>
        <span>Font size</span>
        <div className={styles.fontSizeInput}>
          <Button
            variant='primary'
            onClick={() => changeFontSize(fontSize - 1)}
            disabled={fontSize <= MIN_FONT_SIZE}
          >
            -
          </Button>
          <Input
            className={styles.fontSizeInput2}
            type='number'
            min={MIN_FONT_SIZE}
            max={MAX_FONT_SIZE}
            value={fontSize}
            readOnly
          />
          <Button
            variant='primary'
            onClick={() => changeFontSize(fontSize + 1)}
            disabled={fontSize >= MAX_FONT_SIZE}
          >
            +
          </Button>
        </div>
      </div>
      <div className={styles.optionContainer}>
        <span>Show snippets</span>
        <Switcher
          onChange={() => switchAutocomplete()}
          initialValue={autocomplete}
        />
      </div>
    </div>
  )
}
