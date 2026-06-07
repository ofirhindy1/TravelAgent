import type { CSSProperties } from 'react'
import { COLORS } from '../../../common/colors'

export const outerStyle: CSSProperties = {
  height: '100%',
  overflowY: 'auto',
  overflowX: 'hidden',
}

export const innerStyle: CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '10px',
  padding: '24px 20px',
  minHeight: '100%',
  justifyContent: 'flex-end',
}

export const emptyStateStyle: CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  flex: 1,
  gap: '12px',
  padding: '40px 20px',
  textAlign: 'center',
}

export const emptyHeadlineStyle: CSSProperties = {
  fontSize: '26px',
  fontWeight: 700,
  color: COLORS.textPrimary,
  letterSpacing: '-0.02em',
}

export const emptySublineStyle: CSSProperties = {
  fontSize: '15px',
  color: COLORS.textMuted,
  maxWidth: '320px',
  lineHeight: '1.6',
}
