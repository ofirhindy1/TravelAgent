export type MessageType = 'user' | 'assistant' | 'tool_call' | 'tool_result'

export interface ChatMessage {
  id: string
  type: MessageType
  content: string
  tool?: string
  timestamp: number
  isStreaming?: boolean
}

export type SSEEventType = 'tool_call' | 'tool_result' | 'token' | 'done' | 'error'

export interface SSEEvent {
  type: SSEEventType
  tool?: string
  input?: Record<string, unknown>
  output?: string
  content?: string
  message?: string
}

export interface ChatSession {
  thread_id: string
  title: string
  updated_at: string | null
}
