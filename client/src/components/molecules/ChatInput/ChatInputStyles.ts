import type { CSSProperties } from 'react'
import { COLORS } from '../../../common/colors'

export const containerStyle: CSSProperties = {
  display: 'flex',
  alignItems: 'flex-end',
  gap: '10px',
  padding: '12px 16px 16px',
  background: COLORS.surface,
  borderTop: `1px solid ${COLORS.borderColor}`,
}

export const inputWrapperStyle: CSSProperties = {
  flex: 1,
  minWidth: 0,
}
