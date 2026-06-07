import type { CSSProperties } from 'react'
import { COLORS } from '../../../common/colors'

export const containerStyle: CSSProperties = {
  display: 'flex',
  gap: '5px',
  alignItems: 'center',
  padding: '12px 16px',
}

export const dotStyle: CSSProperties = {
  width: '6px',
  height: '6px',
  borderRadius: '50%',
  backgroundColor: COLORS.sidebarText,
  display: 'inline-block',
}
