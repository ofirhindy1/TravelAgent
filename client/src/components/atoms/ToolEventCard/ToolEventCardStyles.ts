import type { CSSProperties } from 'react'
import { COLORS } from '../../../common/colors'
import { CARD_MAX_CONTENT_HEIGHT } from './ToolEventCardConstants'

type CardType = 'tool_call' | 'tool_result'

export function getCardStyle(type: CardType): CSSProperties {
  const isCall = type === 'tool_call'
  return {
    borderRadius: '10px',
    border: `1px solid ${isCall ? COLORS.toolCallBorder : COLORS.toolResultBorder}`,
    background: isCall ? COLORS.toolCallBg : COLORS.toolResultBg,
    overflow: 'hidden',
    maxWidth: '480px',
    width: '100%',
    boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
  }
}

export function getHeaderStyle(type: CardType): CSSProperties {
  const isCall = type === 'tool_call'
  return {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '8px 14px',
    background: isCall ? COLORS.toolCallHeader : COLORS.toolResultHeader,
    color: isCall ? COLORS.toolCallText : COLORS.toolResultText,
    fontSize: '12px',
    fontWeight: 700,
    letterSpacing: '0.04em',
    textTransform: 'uppercase' as const,
    borderBottom: `1px solid ${isCall ? COLORS.toolCallBorder : COLORS.toolResultBorder}`,
  }
}

export function getContentStyle(type: CardType): CSSProperties {
  return {
    margin: 0,
    padding: '10px 14px',
    fontSize: '12px',
    fontFamily: '"SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace',
    color: type === 'tool_call' ? COLORS.toolCallText : COLORS.toolResultText,
    lineHeight: '1.5',
    maxHeight: CARD_MAX_CONTENT_HEIGHT,
    overflowY: 'auto',
    whiteSpace: 'pre-wrap' as const,
    wordBreak: 'break-word' as const,
    opacity: 0.9,
  }
}
