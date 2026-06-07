import { getCardStyle, getHeaderStyle, getContentStyle } from './ToolEventCardStyles'
import { TOOL_ICONS, TOOL_LABELS } from './ToolEventCardConstants'

interface ToolEventCardProps {
  type: 'tool_call' | 'tool_result'
  tool?: string
  content: string
}

export function ToolEventCard({ type, tool, content }: ToolEventCardProps) {
  return (
    <div style={getCardStyle(type)}>
      <div style={getHeaderStyle(type)}>
        <span>{TOOL_ICONS[type]}</span>
        <span>
          {TOOL_LABELS[type]}{tool ? `: ${tool}` : ''}
        </span>
      </div>
      <pre style={getContentStyle(type)}>{content}</pre>
    </div>
  )
}
