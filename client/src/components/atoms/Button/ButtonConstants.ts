export const BUTTON_VARIANTS = {
  primary: 'primary',
  ghost: 'ghost',
  danger: 'danger',
} as const

export type ButtonVariant = keyof typeof BUTTON_VARIANTS
