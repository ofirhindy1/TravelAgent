import { useState } from 'react'
import { Input } from '../../atoms/Input/Input'
import { Button } from '../../atoms/Button/Button'
import { containerStyle, inputWrapperStyle } from './ChatInputStyles'
import { SEND_ICON, SEND_ARIA_LABEL, STOP_ICON, STOP_ARIA_LABEL } from './ChatInputConstants'
import { INPUT_PLACEHOLDER } from '../../atoms/Input/InputConstants'

interface ChatInputProps {
  onSend: (message: string) => void
  onStop?: () => void
  isStreaming?: boolean
}

export function ChatInput({ onSend, onStop, isStreaming }: ChatInputProps) {
  const [value, setValue] = useState('')

  function handleSend() {
    const trimmed = value.trim()
    if (!trimmed || isStreaming) return
    onSend(trimmed)
    setValue('')
  }

  return (
    <div style={containerStyle}>
      <div style={inputWrapperStyle}>
        <Input
          value={value}
          onChange={e => setValue(e.target.value)}
          onSubmit={handleSend}
          placeholder={INPUT_PLACEHOLDER}
          disabled={isStreaming}
        />
      </div>
      {isStreaming ? (
        <Button
          variant="danger"
          onClick={onStop}
          aria-label={STOP_ARIA_LABEL}
          title={STOP_ARIA_LABEL}
        >
          {STOP_ICON}
        </Button>
      ) : (
        <Button
          onClick={handleSend}
          disabled={!value.trim()}
          aria-label={SEND_ARIA_LABEL}
          title={SEND_ARIA_LABEL}
        >
          {SEND_ICON}
        </Button>
      )}
    </div>
  )
}
