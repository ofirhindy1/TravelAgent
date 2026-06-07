import { ButtonHTMLAttributes, useState } from 'react'
import { getButtonStyle } from './ButtonStyles'
import { BUTTON_VARIANTS, type ButtonVariant } from './ButtonConstants'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
}

export function Button({
  variant = BUTTON_VARIANTS.primary,
  disabled,
  onMouseEnter,
  onMouseLeave,
  style,
  children,
  ...rest
}: ButtonProps) {
  const [hovered, setHovered] = useState(false)

  return (
    <button
      {...rest}
      disabled={disabled}
      style={{ ...getButtonStyle(variant, hovered, disabled), ...style }}
      onMouseEnter={e => { setHovered(true); onMouseEnter?.(e) }}
      onMouseLeave={e => { setHovered(false); onMouseLeave?.(e) }}
    >
      {children}
    </button>
  )
}
