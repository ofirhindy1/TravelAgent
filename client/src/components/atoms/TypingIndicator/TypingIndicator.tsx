import { motion } from 'framer-motion'
import { containerStyle, dotStyle } from './TypingIndicatorStyles'
import { DOTS, DOT_DELAY_SECONDS } from './TypingIndicatorConstants'

export function TypingIndicator() {
  return (
    <div style={containerStyle}>
      {DOTS.map(i => (
        <motion.span
          key={i}
          style={dotStyle}
          animate={{ y: [0, -5, 0] }}
          transition={{
            duration: 0.6,
            repeat: Infinity,
            delay: i * DOT_DELAY_SECONDS,
            ease: 'easeInOut',
          }}
        />
      ))}
    </div>
  )
}
