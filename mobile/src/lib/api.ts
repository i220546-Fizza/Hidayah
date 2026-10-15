import { createClient } from './client'
import { secureStorage } from './secureStorage'

export { ApiError } from './client'

// Set EXPO_PUBLIC_API_BASE_URL in mobile/.env. The default only works in an emulator.
export const BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL ?? 'http://10.0.2.2:8000/api/v1'

export const client = createClient(BASE_URL, secureStorage)
export const api = client.api
