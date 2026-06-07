import { motion } from 'framer-motion'
import { COLORS } from '../../../common/colors'
import { getItemStyle, getTitleStyle, timeStyle } from './SidebarItemStyles'
import { formatRelativeTime } from './SidebarItemConstants'

interface SidebarItemProps {
  threadId: string
  title: string
  updatedAt: string | null
  isActive: boolean
  onClick: () => void
}

export function SidebarItem({ title, updatedAt, isActive, onClick }: SidebarItemProps) {
  return (
    <motion.button
      style={getItemStyle(isActive)}
      onClick={onClick}
      whileHover={isActive ? {} : { backgroundColor: COLORS.sidebarItemHover }}
      transition={{ duration: 0.15 }}
    >
      <span style={getTitleStyle(isActive)}>{title}</span>
      {updatedAt && (
        <span style={timeStyle}>{formatRelativeTime(updatedAt)}</span>
      )}
    </motion.button>
  )
}
