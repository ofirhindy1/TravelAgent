import type { CSSProperties } from 'react'
import { COLORS } from '../../../common/colors'

export const wrapperStyle: CSSProperties = {
  display: 'flex',
  alignItems: 'flex-start',
  gap: '10px',
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
}

export const bubbleStyle: CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '12px',
  background: COLORS.agentBubble,
  border: `1px solid ${COLORS.agentBubbleBorder}`,
  borderRadius: '18px 18px 18px 4px',
  padding: '14px 18px',
}

export const dotsRowStyle: CSSProperties = {
  display: 'flex',
  gap: '5px',
  alignItems: 'center',
}

export const dotStyle: CSSProperties = {
  width: '8px',
  height: '8px',
  borderRadius: '50%',
  background: COLORS.thinkingDot,
  display: 'inline-block',
}

export const labelStyle: CSSProperties = {
  color: COLORS.textMuted,
  fontSize: '13px',
  fontStyle: 'italic',
}
