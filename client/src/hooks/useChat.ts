import { useState, useCallback, useEffect, useRef } from 'react'
import { useMutation } from '@tanstack/react-query'
import { v4 as uuidv4 } from 'uuid'
import type { ChatMessage, SSEEvent } from '../common/types'
import { CHAT_STREAM_URL, CHAT_CANCEL_URL, CHAT_HISTORY_URL, parseSSEBuffer, prettyJSON } from '../functions/streamParser'

export function useChat(threadId: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const abortRef = useRef<AbortController | null>(null)

  // When threadId changes: abort any in-flight stream, clear messages, then
  // load the stored history from the server (display only — no LLM call).
  useEffect(() => {
    abortRef.current?.abort()
    setMessages([])
    let cancelled = false

    fetch(`${CHAT_HISTORY_URL}?thread_id=${encodeURIComponent(threadId)}`)
      .then(r => r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`)))
      .then((raw: Array<{ type: string; content: string; tool?: string }>) => {
        if (cancelled) return
        if (raw.length > 0) {
          setMessages(
            raw.map(m => ({
              id: uuidv4(),
              type: m.type as ChatMessage['type'],
              content: m.content,
              tool: m.tool,
              timestamp: Date.now(),
              isStreaming: false,
            }))
          )
        }
      })
      .catch(err => { if (!cancelled) console.error('[useChat] history fetch failed:', err) })

    return () => { cancelled = true }
  }, [threadId])

  // ── SSE stream processor ───────────────────────────────────────────────
  const processEvent = useCallback((event: SSEEvent) => {
    switch (event.type) {
      case 'tool_call': {
        const content = event.input
          ? prettyJSON(JSON.stringify(event.input))
          : ''
        setMessages(prev => [
          ...prev,
          { id: uuidv4(), type: 'tool_call', content, tool: event.tool, timestamp: Date.now() },
        ])
        break
      }

      case 'tool_result': {
        const content = prettyJSON(event.output ?? '')
        setMessages(prev => [
          ...prev,
          { id: uuidv4(), type: 'tool_result', content, tool: event.tool, timestamp: Date.now() },
        ])
        break
      }

      case 'token': {
        const chunk = event.content ?? ''
        setMessages(prev => {
          const last = prev[prev.length - 1]
          if (last?.type === 'assistant' && last.isStreaming) {
            return [...prev.slice(0, -1), { ...last, content: last.content + chunk }]
          }
          return [
            ...prev.map(m => (m.isStreaming ? { ...m, isStreaming: false } : m)),
            { id: uuidv4(), type: 'assistant' as const, content: chunk, timestamp: Date.now(), isStreaming: true },
          ]
        })
        break
      }

      case 'done': {
        setMessages(prev => {
          const last = prev[prev.length - 1]
          if (last?.type === 'assistant') {
            return [...prev.slice(0, -1), { ...last, isStreaming: false }]
          }
          return prev
        })
        break
      }

      case 'error': {
        setMessages(prev => [
          ...prev.map(m => (m.isStreaming ? { ...m, isStreaming: false } : m)),
          {
            id: uuidv4(),
            type: 'assistant' as const,
            content: `⚠ Error: ${event.message ?? 'Unknown error'}`,
            timestamp: Date.now(),
            isStreaming: false,
          },
        ])
        break
      }
    }
  }, [])

  // ── Core streaming fetch ───────────────────────────────────────────────
  const streamMessage = useCallback(async (userMessage: string) => {
    const controller = new AbortController()
    abortRef.current = controller

    let response: Response
    try {
      response = await fetch(CHAT_STREAM_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ thread_id: threadId, user_message: userMessage }),
        signal: controller.signal,
      })
    } catch (err) {
      // Silently discard intentional aborts (triggered by resetThreadId)
      if (err instanceof DOMException && err.name === 'AbortError') return
      throw err
    }

    if (!response.ok) throw new Error(`Request failed (${response.status})`)
    if (!response.body) throw new Error('Response body is empty')

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const { events, remaining } = parseSSEBuffer(buffer)
        buffer = remaining
        for (const evt of events) processEvent(evt)
      }
      const { events } = parseSSEBuffer(buffer + '\n')
      for (const evt of events) processEvent(evt)
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') return
      throw err
    } finally {
      reader.releaseLock()
    }
  }, [threadId, processEvent])

  // ── React Query mutation (drives isPending / isStreaming) ──────────────
  const mutation = useMutation({ mutationFn: streamMessage })

  const sendMessage = useCallback((content: string) => {
    const trimmed = content.trim()
    if (!trimmed || mutation.isPending) return
    setMessages(prev => [
      ...prev,
      { id: uuidv4(), type: 'user', content: trimmed, timestamp: Date.now() },
    ])
    mutation.mutate(trimmed)
  }, [mutation])

  // Abort the local stream AND tell the server to stop its LLM/tool work.
  const stopStreaming = useCallback(() => {
    abortRef.current?.abort()
    fetch(CHAT_CANCEL_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ thread_id: threadId }),
    }).catch(() => {/* non-critical */})
  }, [threadId])

  return { messages, sendMessage, stopStreaming, isStreaming: mutation.isPending }
}
