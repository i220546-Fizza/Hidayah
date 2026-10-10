import { z } from 'zod'

// The server enforces the real rules; these give instant feedback.
export const loginSchema = z.object({
  email: z.email('Enter a valid email address.'),
  password: z.string().min(1, 'Enter your password.'),
})

export const registerSchema = z.object({
  displayName: z.string().max(120, 'Use 120 characters or fewer.').optional(),
  email: z.email('Enter a valid email address.'),
  password: z.string().min(10, 'Use at least 10 characters.').max(128, 'Use at most 128 characters.'),
})

export type LoginValues = z.infer<typeof loginSchema>
export type RegisterValues = z.infer<typeof registerSchema>
