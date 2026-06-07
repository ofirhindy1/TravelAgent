import type { CSSProperties } from 'react'
import { COLORS } from '../../../common/colors'

export const headerStyle: CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '14px',
  padding: '0 20px',
  height: '64px',
  background: COLORS.headerBg,
  borderBottom: `1px solid ${COLORS.headerBorder}`,
  flexShrink: 0,
}

export const iconWrapperStyle: CSSProperties = {
  width: '40px',
  height: '40px',
  borderRadius: '12px',
  background: 'linear-gradient(135deg, #1d4ed8 0%, #7c3aed 100%)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontSize: '20px',
  flexShrink: 0,
}

export const titleStyle: CSSProperties = {
  fontSize: '18px',
  fontWeight: 700,
  color: COLORS.textPrimary,
  letterSpacing: '-0.01em',
}

export const subtitleStyle: CSSProperties = {
  fontSize: '13px',
  color: COLORS.textMuted,
  marginTop: '1px',
}

export const rightGroupStyle: CSSProperties = {
  marginLeft: 'auto',
  display: 'flex',
  alignItems: 'center',
  gap: '10px',
}

export const threadBadgeStyle: CSSProperties = {
  fontSize: '12px',
  color: COLORS.textPrimary,
  background: COLORS.surface,
  border: `1px solid ${COLORS.borderColor}`,
  borderRadius: '6px',
  padding: '4px 10px',
  fontFamily: 'monospace',
}

export function getNewChatButtonStyle(hovered: boolean): CSSProperties {
  return {
    fontSize: '14px',
    fontWeight: 600,
    color: hovered ? COLORS.userBubble : COLORS.sidebarTextActive,
    background: hovered ? COLORS.userBubbleText : 'transparent',
    border: `1px solid ${COLORS.borderColor}`,
    borderRadius: '8px',
    padding: '6px 14px',
    cursor: 'pointer',
    transition: 'all 0.15s ease',
    outline: 'none',
    fontFamily: 'inherit',
    whiteSpace: 'nowrap' as const,
  }
}
