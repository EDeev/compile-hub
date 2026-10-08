import { useEffect, useRef, useState } from "react"
import CodeMirror from "@uiw/react-codemirror"
import { javascript, javascriptLanguage } from "@codemirror/lang-javascript"
import { python, pythonLanguage } from "@codemirror/lang-python"
import { javaLanguage } from "@codemirror/lang-java"
import { go, goLanguage } from "@codemirror/lang-go"
import { cppLanguage } from "@codemirror/lang-cpp"
import { atomone } from "@uiw/codemirror-theme-atomone"
import { PanelGroup, Panel, PanelResizeHandle } from "react-resizable-panels"
import { CgSpinner } from "react-icons/cg"
import styles from "./Editor.module.css"
import { Button } from "@/components/ui/Button"
import { Console } from "@/components/common/Console"
import { useEditorSettings, useEditorState } from "@/store/editorStore"
import { useUserStore } from "@/store/userStore"
import { extensionOf } from "@/store/languagesStore"
import { fileIcon } from "@/utils/icons"
import { useT } from "@/i18n"
import { useIsMobile } from "@/hooks/useIsMobile"
import { useUiStore } from "@/store/uiStore"

const langExtension = (ext: string, autocomplete: boolean) => {
  switch (ext) {
    case "js":
      return autocomplete ? [javascript()] : [javascriptLanguage]
    case "py":
      return autocomplete ? [python()] : [pythonLanguage]
    case "c":
    case "cpp":
    case "cc":
    case "cxx":
      return [cppLanguage]
    case "go":
      return autocomplete ? [go()] : [goLanguage]
    case "java":
      return [javaLanguage]
    default:
      return []
  }
}

const ACTIVE = new Set(["starting", "queued", "compiling", "running"])

export const Editor = () => {
  const t = useT()
  const containerRef = useRef<HTMLDivElement>(null)
  const [editorHeight, setEditorHeight] = useState("100%")
  const codeRef = useRef<HTMLDivElement>(null)

  const {
    currentFile,
    code,
    stdin,
    savedCode,
    savedStdin,
    isLoadingFile,
    isSaving,
    status,
    position,
    result,
    setCode,
    setStdin,
    save,
    run,
    stop
  } = useEditorState()
  const { fontSize, autocomplete } = useEditorSettings()
  const username = useUserStore((s) => s.currentUser.username)
  const isMobile = useIsMobile()
  const { editorTab, setEditorTab, setFilesOpen } = useUiStore()

  // высота редактора — по панели (CodeMirror нужна явная высота)
  useEffect(() => {
    if (!codeRef.current) return
    const observer = new ResizeObserver(([entry]) =>
      setEditorHeight(`${entry.contentRect.height}px`)
    )
    observer.observe(codeRef.current)
    return () => observer.disconnect()
  }, [currentFile, isMobile])

  // Ctrl+S — сохранить, Ctrl+Enter — запустить
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (!(e.ctrlKey || e.metaKey)) return
      if (e.key === "s") {
        e.preventDefault()
        save()
      } else if (e.key === "Enter") {
        e.preventDefault()
        run()
      }
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [save, run])

  if (!currentFile) {
    return (
      <div ref={containerRef} className={styles.helloMessage}>
        <h1>
          {t("editor.greeting", { name: "" })}
          <span>{username}</span>
        </h1>
        <p>{t(isMobile ? "editor.hintMobile" : "editor.hint")}</p>
        {isMobile && (
          <Button
            variant='secondary'
            className={styles.openFiles}
            onClick={() => setFilesOpen(true)}
          >
            {t("editor.openFiles")}
          </Button>
        )}
      </div>
    )
  }

  const ext = extensionOf(currentFile.name)
  const isModified = code !== savedCode || stdin !== savedStdin
  const isActive = ACTIVE.has(status)

  const onRun = () => {
    if (isMobile) setEditorTab("console") // на телефоне сразу показать консоль
    run()
  }

  const statusText = () => {
    if (status === "queued")
      return t("editor.queued", { position: position + 1 })
    if (status === "compiling") return t("editor.compiling")
    if (status === "running")
      return t(isMobile ? "editor.runningShort" : "editor.running")
    if (status === "finished" && result) {
      const parts = [t(`verdict.${result.verdict}`)]
      if (result.timeMs !== undefined) parts.push(`${result.timeMs} ms`)
      if (result.memoryKb !== undefined)
        parts.push(`${(result.memoryKb / 1024).toFixed(1)} MB`)
      return parts.join(" · ")
    }
    return ""
  }

  const codePane = (
    <div ref={codeRef} className={styles.editorWrapper}>
      {isLoadingFile ? (
        <div className={styles.loadSpinnerContainer}>
          <CgSpinner size={30} className={styles.loadSpinner} />
        </div>
      ) : (
        <CodeMirror
          value={code}
          height={editorHeight}
          extensions={langExtension(ext, autocomplete)}
          theme={atomone}
          onChange={setCode}
          style={{ fontSize }}
        />
      )}
    </div>
  )

  const inputPane = (
    <div className={styles.stdinPanel}>
      <label className={styles.stdinLabel}>{t("editor.stdin")}</label>
      <textarea
        className={styles.stdin}
        value={stdin}
        spellCheck={false}
        placeholder={t("editor.stdinPlaceholder")}
        onChange={(e) => setStdin(e.target.value)}
        style={{ fontSize }}
      />
    </div>
  )

  const statusClass = `${styles.status} ${result && status === "finished" ? styles[result.verdict === "OK" ? "ok" : "bad"] : ""}`

  return (
    <div ref={containerRef} className={styles.editorContainer}>
      <div className={styles.editor}>
        <div className={styles.controlPanel}>
          {fileIcon(ext)}
          <span className={styles.fileName}>
            {currentFile.name}
            {isModified && (
              <span className={styles.modified} title={t("editor.unsaved")}>
                {" "}
                ●
              </span>
            )}
          </span>
          {isActive ? (
            <Button variant='danger' onClick={stop}>
              {t("editor.stop")}
            </Button>
          ) : (
            <Button onClick={onRun} disabled={isLoadingFile} title='Ctrl+Enter'>
              {t("editor.run")}
            </Button>
          )}
          <Button
            variant='secondary'
            onClick={save}
            disabled={!isModified || isSaving}
            title='Ctrl+S'
          >
            {t("editor.save")}
          </Button>
          {!isMobile && (
            <span className={statusClass}>
              {isActive && <CgSpinner className={styles.loadSpinner} />}
              {statusText()}
            </span>
          )}
        </div>

        {isMobile ? (
          <>
            <div className={styles.tabs}>
              {(["code", "input", "console"] as const).map((tab) => (
                <button
                  key={tab}
                  className={`${styles.tab} ${editorTab === tab ? styles.activeTab : ""}`}
                  onClick={() => setEditorTab(tab)}
                >
                  {t(`editor.tab.${tab}`)}
                  {tab === "input" && stdin.trim() !== "" && " •"}
                </button>
              ))}
            </div>
            {statusText() && (
              <div className={`${statusClass} ${styles.mobileStatus}`}>
                {isActive && <CgSpinner className={styles.loadSpinner} />}
                {statusText()}
              </div>
            )}
            {/* все вкладки смонтированы (консоль должна получать вывод), видна одна */}
            <div className={styles.mobilePanes}>
              <div
                className={`${styles.mobilePane} ${editorTab === "code" ? styles.visiblePane : ""}`}
              >
                {codePane}
              </div>
              <div
                className={`${styles.mobilePane} ${editorTab === "input" ? styles.visiblePane : ""}`}
              >
                {inputPane}
              </div>
              <div
                className={`${styles.mobilePane} ${editorTab === "console" ? styles.visiblePane : ""}`}
              >
                <Console />
              </div>
            </div>
          </>
        ) : (
          <PanelGroup direction='horizontal' className={styles.panelGroup}>
            <Panel defaultSize={55} minSize={30} className={styles.codePanel}>
              {codePane}
            </Panel>
            <PanelResizeHandle className={styles.resizeHandle} />
            <Panel minSize={20} className={styles.outputPanel}>
              <PanelGroup direction='vertical'>
                <Panel defaultSize={22} minSize={10}>
                  {inputPane}
                </Panel>
                <PanelResizeHandle className={styles.resizeHandleHorizontal} />
                <Panel minSize={20}>
                  <Console />
                </Panel>
              </PanelGroup>
            </Panel>
          </PanelGroup>
        )}
      </div>
    </div>
  )
}
