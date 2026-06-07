import { useEffect, useState, useCallback, useRef } from 'react'
import { motion } from 'framer-motion'
import type { ChatSession } from '../../../common/types'
import { CHAT_SESSIONS_URL } from '../../../functions/streamParser'
import { COLORS } from '../../../common/colors'
import { SessionList } from '../../molecules/SessionList/SessionList'
import { TypingIndicator } from '../../atoms/TypingIndicator/TypingIndicator'
import { sidebarStyle, headerStyle, titleStyle, newChatStyle } from './SidebarStyles'
import { SIDEBAR_TITLE, NEW_CHAT_LABEL } from './SidebarConstants'

interface SidebarProps {
  activeThreadId: string
  onSelectSession: (threadId: string) => void
  onNewChat: () => void
}

export function Sidebar({ activeThreadId, onSelectSession, onNewChat }: SidebarProps) {
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [loading, setLoading] = useState(true)
  // Only show the loading spinner on the very first fetch; subsequent refreshes
  // are silent so the session list doesn't flash away on every thread switch.
  const isFirstLoad = useRef(true)

  const fetchSessions = useCallback(() => {
    if (isFirstLoad.current) setLoading(true)
    fetch(CHAT_SESSIONS_URL)
      .then(r => (r.ok ? r.json() : []))
      .then((data: ChatSession[]) => setSessions(data))
      .catch(() => setSessions([]))
      .finally(() => {
        setLoading(false)
        isFirstLoad.current = false
      })
  }, [])

  useEffect(() => {
    fetchSessions()
  }, [activeThreadId, fetchSessions])

  return (
    <div style={sidebarStyle}>
      <div style={headerStyle}>
        <p style={titleStyle}>{SIDEBAR_TITLE}</p>
        <motion.button
          style={newChatStyle}
          onClick={onNewChat}
          whileHover={{ backgroundColor: COLORS.sidebarNewChatHover }}
          transition={{ duration: 0.15 }}
        >
          {NEW_CHAT_LABEL}
        </motion.button>
      </div>

      {loading ? (
        <TypingIndicator />
      ) : (
        <SessionList
          sessions={sessions}
          activeThreadId={activeThreadId}
          onSelect={onSelectSession}
        />
      )}
    </div>
  )
}
