import type { CSSProperties } from 'react'
import { COLORS } from '../../../common/colors'

export const listStyle: CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  overflowY: 'auto',
  flex: 1,
}

export const emptyStyle: CSSProperties = {
  padding: '24px 14px',
  fontSize: '13px',
  color: COLORS.textSubtle,
  textAlign: 'center',
  margin: 0,
}
