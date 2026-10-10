/**
 * Decorative hero panel: a pointed arch filled with an eight-pointed-star
 * lattice. Purely visual (aria-hidden); contains no text or sacred content.
 */
export function ArchPanel({ className = '' }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 360 440"
      aria-hidden="true"
      className={className}
      preserveAspectRatio="xMidYMid meet"
    >
      <defs>
        <clipPath id="arch-clip">
          <path d="M20 440V190C20 100 80 40 180 8c100 32 160 92 160 182v250z" />
        </clipPath>
        <pattern id="star-lattice" width="60" height="60" patternUnits="userSpaceOnUse">
          <g fill="none" stroke="#c6a568" strokeWidth="1" opacity="0.55">
            <rect x="15" y="15" width="30" height="30" />
            <rect x="15" y="15" width="30" height="30" transform="rotate(45 30 30)" />
          </g>
          <path d="M0 0h60v60H0z" fill="none" stroke="#a9bdaf" strokeWidth="0.5" opacity="0.25" />
        </pattern>
      </defs>
      <g clipPath="url(#arch-clip)">
        <rect width="360" height="440" fill="#123c32" />
        <rect width="360" height="440" fill="url(#star-lattice)" />
      </g>
      <path
        d="M20 440V190C20 100 80 40 180 8c100 32 160 92 160 182v250"
        fill="none"
        stroke="#c6a568"
        strokeWidth="2"
      />
      <path
        d="M44 440V196C44 118 96 62 180 36c84 26 136 82 136 160v244"
        fill="none"
        stroke="#c6a568"
        strokeWidth="1"
        opacity="0.6"
      />
    </svg>
  )
}
