import type { CSSProperties } from 'react'
import { COLORS } from '../../../common/colors'
import type { ButtonVariant } from './ButtonConstants'

export function getButtonStyle(
  variant: ButtonVariant,
  hovered: boolean,
  disabled?: boolean,
): CSSProperties {
  const base: CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    border: 'none',
    borderRadius: '10px',
    cursor: disabled ? 'not-allowed' : 'pointer',
    fontWeight: 600,
    fontSize: '18px',
    width: '44px',
    height: '44px',
    flexShrink: 0,
    transition: 'background 0.15s ease, transform 0.1s ease',
    outline: 'none',
    opacity: disabled ? 0.45 : 1,
    transform: hovered && !disabled ? 'scale(1.05)' : 'scale(1)',
  }

  if (variant === 'primary') {
    return {
      ...base,
      background: hovered && !disabled ? COLORS.sendBgHover : COLORS.sendBg,
      color: COLORS.sendText,
    }
  }

  if (variant === 'danger') {
    return {
      ...base,
      background: hovered && !disabled ? '#b91c1c' : '#dc2626',
      color: '#ffffff',
    }
  }

  return {
    ...base,
    background: 'transparent',
    color: COLORS.textMuted,
    border: `1px solid ${COLORS.borderColor}`,
  }
}
