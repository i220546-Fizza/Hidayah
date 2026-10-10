/**
 * Hidayah design tokens for the mobile app.
 * Mirrors frontend/src/styles/tokens.css. Change both together.
 */
export const colors = {
  emerald: '#123C32',
  ivory: '#F8F5ED',
  gold: '#C6A568',
  sand: '#E9E2D4',
  charcoal: '#26352F',
  white: '#FFFFFF',
  sage: '#A9BDAF',
  bronze: '#8B6B47',
  terracotta: '#B85C50',
} as const

export const fonts = {
  display: 'PlayfairDisplay',
  sans: 'Inter',
  arabic: 'Amiri',
  urdu: 'NotoNastaliqUrdu',
} as const

export const radius = { sm: 6, md: 10 } as const

export const spacing = { xs: 4, sm: 8, md: 16, lg: 24, xl: 40 } as const

/** Minimum touch target, in points (platform accessibility guidance). */
export const minTouchTarget = 44
