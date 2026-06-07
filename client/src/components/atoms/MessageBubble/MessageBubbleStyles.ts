import type { CSSProperties } from 'react'
import { COLORS } from '../../../common/colors'
import { BUBBLE_MAX_WIDTH, BORDER_RADIUS } from './MessageBubbleConstants'

export function getBubbleStyle(type: 'user' | 'assistant'): CSSProperties {
  const isUser = type === 'user'
  return {
    maxWidth: BUBBLE_MAX_WIDTH,
    padding: '12px 16px',
    borderRadius: isUser ? BORDER_RADIUS.user : BORDER_RADIUS.assistant,
    background: isUser ? COLORS.userBubble : COLORS.agentBubble,
    border: isUser ? 'none' : `1px solid ${COLORS.agentBubbleBorder}`,
    boxShadow: '0 2px 8px rgba(0,0,0,0.25)',
  }
}

export function getTextStyle(type: 'user' | 'assistant'): CSSProperties {
  return {
    color: type === 'user' ? COLORS.userBubbleText : COLORS.agentBubbleText,
    fontSize: '15px',
    lineHeight: '1.65',
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
    margin: 0,
  }
}

export const avatarStyle: CSSProperties = {
  width: '32px',
  height: '32px',
  borderRadius: '50%',
  background: 'linear-gradient(135deg, #1d4ed8, #7c3aed)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontSize: '14px',
  flexShrink: 0,
  marginTop: '2px',
}
