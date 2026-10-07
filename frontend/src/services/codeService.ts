interface CompilationResult {
  success: boolean
  output?: string
  requiresInput?: boolean
  error?: string
  details?: {
    line?: number
    message?: string
    [key: string]: any
  }
  inputDescription?: {
    variables: Array<{
      name: string
      type: string
      description: string
    }>
  }
  executionTime?: number
}

export const CodeService = {
  async fetchCode(fileId: number): Promise<string> {
    const response = await fetch(`/api/code?fileId=${fileId}`)
    if (!response.ok) {
      throw new Error(`Failed to fetch code: ${response.status}`)
    }
    return (await response.json()) as string
  },

  async compileCode(code: string): Promise<CompilationResult> {
    const response = await fetch(`/api/compile/?code=${code}`)
    console.log("запрос на компиляцию")
    if (!response.ok) {
      throw new Error(`Failed to compile code: ${response.status}`)
    }
    return (await response.json()) as CompilationResult
  },

  async compileWithInput(code: string, input: string): Promise<string> {
    const response = await fetch(`/api/compile/?code=${code}?input=${input}`)
    if (!response.ok) {
      throw new Error(`Failed to compile code: ${response.status}`)
    }
    return (await response.json()) as string
  }
}
