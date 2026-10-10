export type User = {
  id: string
  email: string
  display_name: string | null
  email_verified: boolean
  roles: string[]
  created_at: string
}

export type AuthStatus = 'loading' | 'authenticated' | 'anonymous'
