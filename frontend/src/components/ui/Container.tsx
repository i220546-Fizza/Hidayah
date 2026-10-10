import type { ElementType, HTMLAttributes } from 'react'

type ContainerProps = HTMLAttributes<HTMLElement> & { as?: ElementType }

export function Container({ as: Tag = 'div', className = '', ...props }: ContainerProps) {
  return <Tag className={`mx-auto w-full max-w-6xl px-5 sm:px-8 ${className}`} {...props} />
}
