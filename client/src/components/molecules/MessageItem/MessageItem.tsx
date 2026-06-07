import type { ChatMessage } from '../../../common/types'
import { MessageBubble } from '../../atoms/MessageBubble/MessageBubble'
import { ToolEventCard } from '../../atoms/ToolEventCard/ToolEventCard'
import { userWrapperStyle, agentWrapperStyle, toolWrapperStyle } from './MessageItemStyles'

interface MessageItemProps {
  message: ChatMessage
}

export function MessageItem({ message }: MessageItemProps) {
  if (message.type === 'user') {
    return (
      <div style={userWrapperStyle}>
        <MessageBubble type="user" content={message.content} />
      </div>
    )
  }

  if (message.type === 'assistant') {
    return (
      <div style={agentWrapperStyle}>
        <MessageBubble
          type="assistant"
          content={message.content}
          isStreaming={message.isStreaming}
        />
      </div>
    )
  }

  // tool_call or tool_result
  return (
    <div style={toolWrapperStyle}>
      <ToolEventCard type={message.type} tool={message.tool} content={message.content} />
    </div>
  )
}
