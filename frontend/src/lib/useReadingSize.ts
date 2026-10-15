import { useState } from 'react'

const KEY = 'hidayah.arabicSize'
const SIZES = ['text-2xl', 'text-3xl', 'text-4xl', 'text-5xl'] as const

function load(): number {
  try {
    const n = Number(localStorage.getItem(KEY))
    return Number.isInteger(n) && n >= 0 && n < SIZES.length ? n : 1
  } catch {
    return 1
  }
}

/** Remembers the reader's Arabic text size on this device (best effort). */
export function useArabicSize() {
  const [i, setI] = useState(load)
  const set = (n: number) => {
    const v = Math.max(0, Math.min(SIZES.length - 1, n))
    setI(v)
    try {
      localStorage.setItem(KEY, String(v))
    } catch {
      /* storage unavailable: size still works for this visit */
    }
  }
  return { className: SIZES[i], bigger: () => set(i + 1), smaller: () => set(i - 1), canBigger: i < SIZES.length - 1, canSmaller: i > 0 }
}
