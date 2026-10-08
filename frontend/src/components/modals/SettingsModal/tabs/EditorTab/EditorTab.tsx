import { Input } from "@/components/ui/Input"
import { Button } from "@/components/ui/Button"
import { Switcher } from "@/components/ui/Switcher"
import { useEditorSettings } from "@/store/editorStore"
import { AuthService } from "@/services/authService"
import { useT } from "@/i18n"
import styles from "./EditorTab.module.css"

const MIN_FONT_SIZE = 12
const MAX_FONT_SIZE = 24

export const EditorTab = () => {
  const t = useT()
  const { fontSize, changeFontSize, autocomplete, switchAutocomplete } =
    useEditorSettings()

  const setFont = (size: number) => {
    changeFontSize(size)
    AuthService.saveSettings({ fontSize: size }).catch(() => {})
  }

  return (
    <div className={styles.mainContainer}>
      <h2 className='settingsTitle'>{t("settings.editorTitle")}</h2>
      <div className={styles.optionContainer}>
        <span>{t("settings.fontSize")}</span>
        <div className={styles.fontSizeInput}>
          <Button
            variant='primary'
            onClick={() => setFont(fontSize - 1)}
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
            onClick={() => setFont(fontSize + 1)}
            disabled={fontSize >= MAX_FONT_SIZE}
          >
            +
          </Button>
        </div>
      </div>
      <div className={styles.optionContainer}>
        <span>{t("settings.snippets")}</span>
        <Switcher
          onChange={(value) => {
            switchAutocomplete()
            AuthService.saveSettings({ autocomplete: value }).catch(() => {})
          }}
          initialValue={autocomplete}
        />
      </div>
    </div>
  )
}
