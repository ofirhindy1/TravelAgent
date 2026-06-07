import { useState, useCallback } from 'react'
import { v4 as uuidv4 } from 'uuid'

const STORAGE_KEY = 'travel_agent_thread_id'

interface UseThreadIdReturn {
  threadId: string
  resetThreadId: () => string
  switchThreadId: (id: string) => void
}

export function useThreadId(): UseThreadIdReturn {
  const [threadId, setThreadId] = useState<string>(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) return stored
    const fresh = uuidv4()
    localStorage.setItem(STORAGE_KEY, fresh)
    return fresh
  })

  const resetThreadId = useCallback((): string => {
    const fresh = uuidv4()
    localStorage.setItem(STORAGE_KEY, fresh)
    setThreadId(fresh)
    return fresh
  }, [])

  const switchThreadId = useCallback((id: string): void => {
    localStorage.setItem(STORAGE_KEY, id)
    setThreadId(id)
  }, [])

  return { threadId, resetThreadId, switchThreadId }
}
