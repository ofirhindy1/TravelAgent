import type { SSEEvent } from '../common/types'

export const CHAT_STREAM_URL   = '/chat/stream'
export const CHAT_CANCEL_URL   = '/chat/cancel'
export const CHAT_HISTORY_URL  = '/chat/history'
export const CHAT_SESSIONS_URL = '/chat/sessions'

/**
 * Parse a raw SSE line buffer into individual SSEEvent objects.
 */
export function parseSSEBuffer(raw: string): {
  events: SSEEvent[]
  remaining: string
} {
  const lines = raw.split('\n')
  const remaining = lines.pop() ?? ''
  const events: SSEEvent[] = []

  for (const line of lines) {
    if (!line.startsWith('data: ')) continue
    const payload = line.slice(6).trim()
    if (!payload) continue
    try {
      events.push(JSON.parse(payload) as SSEEvent)
    } catch {
      // Malformed JSON — skip silently
    }
  }

  return { events, remaining }
}

/**
 * Pretty-print a JSON string for display inside a ToolEventCard.
 */
export function prettyJSON(raw: string): string {
  try {
    return JSON.stringify(JSON.parse(raw), null, 2)
  } catch {
    return raw
  }
}
