import type { SVGProps } from 'react'

/**
 * Hidayah emblem: a pointed arch holding an eight-pointed star
 * (two overlapping squares). Uses currentColor so it works on
 * ivory, white and emerald backgrounds.
 */
export function Emblem({ title, ...props }: SVGProps<SVGSVGElement> & { title?: string }) {
  return (
    <svg
      viewBox="0 0 64 64"
      fill="none"
      role={title ? 'img' : undefined}
      aria-hidden={title ? undefined : true}
      aria-label={title}
      {...props}
    >
      <path
        d="M10 58V30C10 17 19 8 32 4c13 4 22 13 22 26v28"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinejoin="round"
      />
      <g stroke="currentColor" strokeWidth="2" strokeLinejoin="round">
        <rect x="21" y="24" width="22" height="22" />
        <rect x="21" y="24" width="22" height="22" transform="rotate(45 32 35)" />
      </g>
    </svg>
  )
}
