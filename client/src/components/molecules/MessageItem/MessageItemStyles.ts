import type { CSSProperties } from 'react'
import {
  USER_WRAPPER_JUSTIFY,
  AGENT_WRAPPER_JUSTIFY,
  TOOL_WRAPPER_JUSTIFY,
} from './MessageItemConstants'

const base: CSSProperties = {
  display: 'flex',
  width: '100%',
  padding: '4px 0',
}

export const userWrapperStyle: CSSProperties = {
  ...base,
  justifyContent: USER_WRAPPER_JUSTIFY,
}

export const agentWrapperStyle: CSSProperties = {
  ...base,
  justifyContent: AGENT_WRAPPER_JUSTIFY,
}

export const toolWrapperStyle: CSSProperties = {
  ...base,
  justifyContent: TOOL_WRAPPER_JUSTIFY,
}
