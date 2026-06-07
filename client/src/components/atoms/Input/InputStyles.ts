import type { CSSProperties } from 'react'
import { COLORS } from '../../../common/colors'

export function getInputStyle(focused: boolean): CSSProperties {
  return {
    width: '100%',
    background: COLORS.inputBg,
    color: COLORS.inputText,
    border: `1.5px solid ${focused ? COLORS.inputBorderFocus : COLORS.inputBorder}`,
    borderRadius: '12px',
    padding: '12px 16px',
    fontSize: '15px',
    lineHeight: '1.5',
    resize: 'none',
    outline: 'none',
    fontFamily: 'inherit',
    transition: 'border-color 0.15s ease',
    overflowY: 'hidden',
  }
}

export const placeholderStyle: CSSProperties = {
  color: COLORS.inputPlaceholder,
}
