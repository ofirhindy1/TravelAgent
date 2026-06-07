import { motion } from 'framer-motion'
import { getBubbleStyle, getTextStyle, avatarStyle } from './MessageBubbleStyles'

interface MessageBubbleProps {
  type: 'user' | 'assistant'
  content: string
  isStreaming?: boolean
}

export function MessageBubble({ type, content, isStreaming }: MessageBubbleProps) {
  const isAssistant = type === 'assistant'

  return (
    <motion.div
      style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, ease: 'easeOut' }}
    >
      {isAssistant && (
        <div style={avatarStyle} aria-hidden="true">✈</div>
      )}
      <div style={getBubbleStyle(type)}>
        <p dir="auto" style={getTextStyle(type)}>
          {content}
          {isStreaming && <span className="stream-cursor">▋</span>}
        </p>
      </div>
    </motion.div>
  )
}
