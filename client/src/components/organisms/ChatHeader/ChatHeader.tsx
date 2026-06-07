import { useState } from 'react'
import {
  headerStyle,
  iconWrapperStyle,
  titleStyle,
  subtitleStyle,
  rightGroupStyle,
  threadBadgeStyle,
  getNewChatButtonStyle,
} from './ChatHeaderStyles'
import { APP_TITLE, APP_SUBTITLE, APP_ICON, NEW_CHAT_LABEL, NEW_CHAT_ARIA } from './ChatHeaderConstants'

interface ChatHeaderProps {
  threadId: string
  onNewChat: () => void
}

export function ChatHeader({ threadId, onNewChat }: ChatHeaderProps) {
  const [hovered, setHovered] = useState(false)

  return (
    <header style={headerStyle}>
      <div style={iconWrapperStyle} aria-hidden="true">{APP_ICON}</div>
      <div>
        <p style={titleStyle}>{APP_TITLE}</p>
        {APP_SUBTITLE && <p style={subtitleStyle}>{APP_SUBTITLE}</p>}
      </div>

      <div style={rightGroupStyle}>
        <button
          style={getNewChatButtonStyle(hovered)}
          onClick={onNewChat}
          aria-label={NEW_CHAT_ARIA}
          onMouseEnter={() => setHovered(true)}
          onMouseLeave={() => setHovered(false)}
        >
          {NEW_CHAT_LABEL}
        </button>
        <span style={threadBadgeStyle} title={`Thread: ${threadId}`}>
          #{threadId.slice(0, 8)}
        </span>
      </div>
    </header>
  )
}
