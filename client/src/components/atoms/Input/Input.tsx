import { TextareaHTMLAttributes, useState, useEffect, useRef, KeyboardEvent } from 'react'
import { getInputStyle } from './InputStyles'
import { INPUT_MAX_HEIGHT_PX, INPUT_SUBMIT_KEY } from './InputConstants'

interface InputProps extends Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, 'onSubmit'> {
  onSubmit?: () => void
}

export function Input({ onSubmit, onChange, value, style, ...rest }: InputProps) {
  const [focused, setFocused] = useState(false)
  const ref = useRef<HTMLTextAreaElement>(null)

  // Auto-resize the textarea up to INPUT_MAX_HEIGHT_PX
  useEffect(() => {
    const el = ref.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, INPUT_MAX_HEIGHT_PX) + 'px'
    el.style.overflowY = el.scrollHeight > INPUT_MAX_HEIGHT_PX ? 'auto' : 'hidden'
  }, [value])

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === INPUT_SUBMIT_KEY && !e.shiftKey) {
      e.preventDefault()
      onSubmit?.()
    }
    rest.onKeyDown?.(e)
  }

  return (
    <textarea
      ref={ref}
      {...rest}
      dir="auto"
      value={value}
      onChange={onChange}
      onKeyDown={handleKeyDown}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
      rows={1}
      style={{ ...getInputStyle(focused), ...style }}
    />
  )
}
