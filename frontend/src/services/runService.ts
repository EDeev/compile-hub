import { api } from "@/api/client"
import type { Language, RunCreated, RunEvent } from "@/api/types"

export interface RunRequest {
  language: string
  code: string
  stdin: string
  fileId: number | null
  interactive: boolean
}

export interface RunStream {
  sendInput: (data: string) => void
  endInput: () => void
  kill: () => void
  close: () => void
}

export const RunService = {
  languages: () => api<Language[]>("/languages"),

  create: (request: RunRequest) => api<RunCreated>("/runs", { method: "POST", body: request }),

  /** Поток событий запуска по WebSocket; onClose — соединение закрыто (после exit или обрыва). */
  stream(
    created: RunCreated,
    onEvent: (event: RunEvent) => void,
    onClose: (finished: boolean) => void
  ): RunStream {
    const scheme = window.location.protocol === "https:" ? "wss" : "ws"
    const url = `${scheme}://${window.location.host}/api/runs/${created.runId}/stream?t=${encodeURIComponent(created.streamToken)}`
    const ws = new WebSocket(url)
    let finished = false
    const queue: string[] = []

    ws.onopen = () => queue.splice(0).forEach((m) => ws.send(m))
    ws.onmessage = (message) => {
      const event = JSON.parse(message.data as string) as RunEvent
      if (event.type === "exit") finished = true
      onEvent(event)
    }
    ws.onclose = () => onClose(finished)

    const send = (payload: object) => {
      const text = JSON.stringify(payload)
      if (ws.readyState === WebSocket.OPEN) ws.send(text)
      else if (ws.readyState === WebSocket.CONNECTING) queue.push(text)
    }
    return {
      sendInput: (data) => send({ type: "stdin", data }),
      endInput: () => send({ type: "eof" }),
      kill: () => send({ type: "kill" }),
      close: () => ws.close()
    }
  }
}
