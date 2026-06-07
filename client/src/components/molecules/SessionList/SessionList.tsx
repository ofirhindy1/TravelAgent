import { AnimatePresence, motion } from 'framer-motion'
import type { ChatSession } from '../../../common/types'
import { SidebarItem } from '../../atoms/SidebarItem/SidebarItem'
import { listStyle, emptyStyle } from './SessionListStyles'
import { EMPTY_LABEL } from './SessionListConstants'

interface SessionListProps {
  sessions: ChatSession[]
  activeThreadId: string
  onSelect: (threadId: string) => void
}

export function SessionList({ sessions, activeThreadId, onSelect }: SessionListProps) {
  if (sessions.length === 0) {
    return <p style={emptyStyle}>{EMPTY_LABEL}</p>
  }

  return (
    <div style={listStyle}>
      <AnimatePresence initial={false}>
        {sessions.map(session => (
          <motion.div
            key={session.thread_id}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -8 }}
            transition={{ duration: 0.18 }}
          >
            <SidebarItem
              threadId={session.thread_id}
              title={session.title}
              updatedAt={session.updated_at}
              isActive={session.thread_id === activeThreadId}
              onClick={() => onSelect(session.thread_id)}
            />
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
}
