import type { CSSProperties } from 'react'
import { COLORS } from '../../../common/colors'

export function getItemStyle(isActive: boolean): CSSProperties {
  return {
    display: 'flex',
    flexDirection: 'column',
    gap: '3px',
    padding: '10px 14px 10px 12px',
    cursor: 'pointer',
    backgroundColor: isActive ? COLORS.sidebarItemActive : 'transparent',
    borderTop: 'none',
    borderRight: 'none',
    borderBottom: 'none',
    borderLeft: isActive ? '2px solid #3b82f6' : '2px solid transparent',
    width: '100%',
    textAlign: 'left',
    boxSizing: 'border-box',
    outline: 'none',
  }
}

export function getTitleStyle(isActive: boolean): CSSProperties {
  return {
    fontSize: '15px',
    color: isActive ? COLORS.sidebarTextActive : '#96a8cc',
    fontWeight: isActive ? 500 : 400,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
    maxWidth: '100%',
  }
}

export const timeStyle: CSSProperties = {
  fontSize: '12px',
  color: '#5a6d9a',
}
