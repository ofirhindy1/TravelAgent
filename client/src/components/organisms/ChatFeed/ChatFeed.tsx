import { useEffect, useRef } from 'react'
import type { ChatMessage } from '../../../common/types'
import { MessageItem } from '../../molecules/MessageItem/MessageItem'
import { ThinkingIndicator } from '../../atoms/ThinkingIndicator/ThinkingIndicator'
import {
  outerStyle,
  innerStyle,
  emptyStateStyle,
  emptyHeadlineStyle,
  emptySublineStyle,
} from './ChatFeedStyles'
import {
  EMPTY_HEADLINE,
  EMPTY_SUBLINE,
  FEED_SCROLL_CLASS,
} from './ChatFeedConstants'

interface ChatFeedProps {
  messages: ChatMessage[]
  isStreaming: boolean
}

export function ChatFeed({ messages, isStreaming }: ChatFeedProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, isStreaming])

  // Show ThinkingIndicator while streaming but no assistant text bubble yet
  const lastMsg = messages[messages.length - 1]
  const showThinking =
    isStreaming && !(lastMsg?.type === 'assistant' && lastMsg?.isStreaming)

  return (
    <div style={outerStyle} className={FEED_SCROLL_CLASS}>
      <div style={innerStyle}>
        {messages.length === 0 ? (
          <div style={emptyStateStyle}>
            <p style={emptyHeadlineStyle}>{EMPTY_HEADLINE}</p>
            <p style={emptySublineStyle}>{EMPTY_SUBLINE}</p>
          </div>
        ) : (
          messages.map(msg => <MessageItem key={msg.id} message={msg} />)
        )}

        {showThinking && <ThinkingIndicator />}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
