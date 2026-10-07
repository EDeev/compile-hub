import { useState, useRef, useEffect } from "react"
import CodeMirror from "@uiw/react-codemirror"
import { javascript, javascriptLanguage } from "@codemirror/lang-javascript"
import { python, pythonLanguage } from "@codemirror/lang-python"
import { java, javaLanguage } from "@codemirror/lang-java"
import { useUserStore } from "@/store/userStore"
import { go, goLanguage } from "@codemirror/lang-go"
import { cpp, cppLanguage } from "@codemirror/lang-cpp"
import { atomone } from "@uiw/codemirror-theme-atomone"
import { PanelGroup, Panel, PanelResizeHandle } from "react-resizable-panels"
import styles from "./Editor.module.css"
import { Button } from "@/components/ui/Button"
import { useEditorState } from "@/store/editorStore"
import { useEditorSettings } from "@/store/editorStore"
import { CgSpinner } from "react-icons/cg"
import { Icons } from "@/utils/icons"

export const Editor = () => {
  const containerRef = useRef<HTMLDivElement>(null)
  const [editorHeight, setEditorHeight] = useState("100%")

  // авторесайз редактора
  useEffect(() => {
    if (!containerRef.current) return

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setEditorHeight(`${entry.contentRect.height}px`)
      }
    })

    resizeObserver.observe(containerRef.current)
    return () => resizeObserver.disconnect()
  }, [])

  const {
    code,
    compileCode,
    output,
    isCompiling,
    setCode,
    awaitsInput,
    currentFile
  } = useEditorState()

  const { fontSize, autocomplete } = useEditorSettings()

  const username = useUserStore().currentUser.username

  if (!currentFile) {
    return (
      <>
        <div ref={containerRef} className={styles.helloMessage}>
          <h1>
            Good morning, <span>{username}</span>
          </h1>
          <p>
            Click the file to open it or create new one by clicking button in
            the left-bottom corner
          </p>
        </div>
      </>
    )
  }

  const getLangExtension = (language: string) => {
    switch (language) {
      case "js":
        return autocomplete ? [javascript()] : [javascriptLanguage]
      case "py":
        return autocomplete ? [python()] : [pythonLanguage]
      case "cpp":
        return [cppLanguage]
      case "go":
        return autocomplete ? [go()] : [goLanguage]
      case "java":
        return [javaLanguage]
    }
  }

  const getFileIcon = (ext: string) => {
    switch (ext) {
      case "py":
        return <img src={Icons.pythonIcon} />
      case "go":
        return <img src={Icons.goIcon} />
      case "java":
        return <img src={Icons.javaIcon} />
      case "cpp":
        return <img src={Icons.cppIcon} />
      case "js":
        return <img src={Icons.jsIcon} />
    }
  }

  const currentFileExt = currentFile.name.split(".")[1]

  return (
    <>
      <div ref={containerRef} className={styles.editorContainer}>
        <div className={styles.editor}>
          <div className={styles.controlPanel}>
            {getFileIcon(currentFileExt)}
            <span className={styles.fileName}>{currentFile?.name}</span>
            <Button onClick={compileCode} disabled={isCompiling}>
              Run
            </Button>
            <Button variant='secondary' onClick={() => console.log("saving..")}>
              Save
            </Button>
          </div>
          <PanelGroup direction='horizontal' className={styles.panelGroup}>
            {/* Редактор кода */}
            <Panel defaultSize={50} minSize={30} className={styles.codePanel}>
              <div className={styles.editorWrapper}>
                <CodeMirror
                  value={code}
                  height={editorHeight}
                  extensions={getLangExtension(currentFileExt)}
                  theme={atomone}
                  onChange={(value) => setCode(value)}
                  className={styles.editor}
                  style={{ fontSize: fontSize }}
                />
              </div>
            </Panel>
            <PanelResizeHandle className={styles.resizeHandle} />
            {/* Консоль вывода */}
            <Panel minSize={20} className={styles.outputPanel}>
              {output && <pre className={styles.consoleOutput}>{output}</pre>}
              {isCompiling && (
                <div className={styles.loadSpinnerContainer}>
                  <CgSpinner size={30} className={styles.loadSpinner} />
                </div>
              )}
            </Panel>
          </PanelGroup>
        </div>
      </div>
    </>
  )
}
