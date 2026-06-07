import type { ChatMessage } from '../../../common/types'
import { ChatHeader } from '../../organisms/ChatHeader/ChatHeader'
import { ChatFeed } from '../../organisms/ChatFeed/ChatFeed'
import { ChatInput } from '../../molecules/ChatInput/ChatInput'
import { templateStyle, feedSectionStyle } from './ChatTemplateStyles'
import { TEMPLATE_TEST_ID } from './ChatTemplateConstants'

interface ChatTemplateProps {
  messages: ChatMessage[]
  isStreaming: boolean
  threadId: string
  onSendMessage: (content: string) => void
  onNewChat: () => void
  onStop: () => void
}

export function ChatTemplate({
  messages,
  isStreaming,
  threadId,
  onSendMessage,
  onNewChat,
  onStop,
}: ChatTemplateProps) {
  return (
    <div style={templateStyle} data-testid={TEMPLATE_TEST_ID}>
      <ChatHeader threadId={threadId} onNewChat={onNewChat} />
      <div style={feedSectionStyle}>
        <ChatFeed messages={messages} isStreaming={isStreaming} />
      </div>
      <ChatInput onSend={onSendMessage} onStop={onStop} isStreaming={isStreaming} />
    </div>
  )
}
