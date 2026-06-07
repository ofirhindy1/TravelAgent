import { useCallback } from 'react'
import { useChat } from '../../hooks/useChat'
import { useThreadId } from '../../hooks/useThreadId'
import { ChatTemplate } from '../../components/templates/ChatTemplate/ChatTemplate'
import { Sidebar } from '../../components/organisms/Sidebar/Sidebar'
import { pageStyle, chatAreaStyle } from './AgentPageStyles'

/**
 * AgentPage — the single page of the app.
 *
 * Owns session lifecycle:
 *  - threadId management (persisted in localStorage)
 *  - SSE streaming via useChat
 *  - New-chat flow: resets threadId → useChat auto-clears → backend cleanup
 *  - Session switching via sidebar
 */
export function AgentPage() {
  const { threadId, resetThreadId, switchThreadId } = useThreadId()
  const { messages, sendMessage, stopStreaming, isStreaming } = useChat(threadId)

  const handleNewChat = useCallback(() => {
    resetThreadId()                       // generates new UUID → useChat resets
  }, [resetThreadId])

  return (
    <div style={pageStyle}>
      <Sidebar
        activeThreadId={threadId}
        onSelectSession={switchThreadId}
        onNewChat={handleNewChat}
      />
      <div style={chatAreaStyle}>
        <ChatTemplate
          messages={messages}
          isStreaming={isStreaming}
          threadId={threadId}
          onSendMessage={sendMessage}
          onNewChat={handleNewChat}
          onStop={stopStreaming}
        />
      </div>
    </div>
  )
}
