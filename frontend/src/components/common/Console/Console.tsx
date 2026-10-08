import { useEffect, useRef } from "react"
import { Terminal } from "@xterm/xterm"
import { FitAddon } from "@xterm/addon-fit"
import "@xterm/xterm/css/xterm.css"
import { setConsoleSink, useEditorState } from "@/store/editorStore"
import { useEditorSettings } from "@/store/editorStore"
import styles from "./Console.module.css"

const ACTIVE = new Set(["starting", "queued", "compiling", "running"])

/**
 * Консоль запуска. Вывод пишет стор редактора; ввод — построчно с локальным эхом, как в терминале:
 * Enter отправляет строку, Backspace стирает, Ctrl+D — конец ввода, Ctrl+C — остановить программу.
 */
export const Console = () => {
  const containerRef = useRef<HTMLDivElement>(null)
  const fontSize = useEditorSettings((s) => s.fontSize)
  const termRef = useRef<Terminal | null>(null)

  useEffect(() => {
    if (!containerRef.current) return
    const term = new Terminal({
      convertEol: false,
      cursorBlink: true,
      fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
      fontSize: useEditorSettings.getState().fontSize,
      scrollback: 5000,
      theme: { background: "#272b33", foreground: "#d4d8df", cursor: "#61afef" }
    })
    const fit = new FitAddon()
    term.loadAddon(fit)
    term.open(containerRef.current)
    fit.fit()
    termRef.current = term

    let line = ""
    setConsoleSink({
      write: (text) => term.write(text),
      clear: () => {
        line = ""
        term.reset()
      }
    })

    const input = term.onData((data) => {
      const { status, interactive, sendInput, endInput, stop } =
        useEditorState.getState()
      if (!ACTIVE.has(status)) return
      if (data === "\x03") return stop() // Ctrl+C
      if (!interactive) return
      for (const ch of data) {
        if (ch === "\r") {
          term.write("\r\n")
          sendInput(line + "\n")
          line = ""
        } else if (ch === "\x7f") {
          if (line) {
            line = line.slice(0, -1)
            term.write("\b \b")
          }
        } else if (ch === "\x04") {
          if (line) sendInput(line)
          line = ""
          endInput()
        } else if (ch >= " ") {
          line += ch
          term.write(ch)
        }
      }
    })

    const observer = new ResizeObserver(() => fit.fit())
    observer.observe(containerRef.current)
    return () => {
      observer.disconnect()
      input.dispose()
      setConsoleSink(null)
      term.dispose()
      termRef.current = null
    }
  }, [])

  useEffect(() => {
    if (termRef.current) termRef.current.options.fontSize = fontSize
  }, [fontSize])

  return (
    <div
      ref={containerRef}
      className={styles.console}
      onClick={() => termRef.current?.focus()}
    />
  )
}
