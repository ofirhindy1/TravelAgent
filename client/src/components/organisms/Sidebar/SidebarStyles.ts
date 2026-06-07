import type { CSSProperties } from 'react'
import { COLORS } from '../../../common/colors'
import { SIDEBAR_WIDTH } from './SidebarConstants'

export const sidebarStyle: CSSProperties = {
  width: SIDEBAR_WIDTH,
  minWidth: SIDEBAR_WIDTH,
  height: '100%',
  backgroundColor: COLORS.sidebarBg,
  borderRight: `1px solid ${COLORS.sidebarBorder}`,
  display: 'flex',
  flexDirection: 'column',
  overflow: 'hidden',
}

export const headerStyle: CSSProperties = {
  padding: '16px 14px 12px',
  borderBottom: `1px solid ${COLORS.sidebarBorder}`,
  display: 'flex',
  flexDirection: 'column',
  gap: '10px',
}

export const titleStyle: CSSProperties = {
  fontSize: '13px',
  fontWeight: 600,
  letterSpacing: '0.06em',
  textTransform: 'uppercase',
  color: COLORS.sidebarTextActive,
  margin: 0,
}

export const newChatStyle: CSSProperties = {
  padding: '9px 14px',
  borderRadius: '8px',
  backgroundColor: COLORS.sidebarNewChatBg,
  color: COLORS.sidebarTextActive,
  fontSize: '15px',
  fontWeight: 500,
  border: 'none',
  cursor: 'pointer',
  textAlign: 'left',
  width: '100%',
  outline: 'none',
}
