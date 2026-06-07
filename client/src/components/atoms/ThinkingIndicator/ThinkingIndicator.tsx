import {
  wrapperStyle,
  avatarStyle,
  bubbleStyle,
  dotsRowStyle,
  dotStyle,
  labelStyle,
} from './ThinkingIndicatorStyles'
import { THINKING_DOT_CLASS, DOT_DELAYS, THINKING_LABEL } from './ThinkingIndicatorConstants'

export function ThinkingIndicator() {
  return (
    <div style={wrapperStyle}>
      <div style={avatarStyle} aria-hidden="true">✈</div>
      <div style={bubbleStyle}>
        <div style={dotsRowStyle}>
          {DOT_DELAYS.map((delay, i) => (
            <span
              key={i}
              className={THINKING_DOT_CLASS}
              style={{ ...dotStyle, animationDelay: delay }}
            />
          ))}
        </div>
        <span style={labelStyle}>{THINKING_LABEL}</span>
      </div>
    </div>
  )
}
