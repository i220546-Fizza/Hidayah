import * as SecureStore from 'expo-secure-store'
import type { TokenStorage } from './client'

const KEY = 'hidayah.refresh'

export const secureStorage: TokenStorage = {
  get: () => SecureStore.getItemAsync(KEY),
  set: (t) => SecureStore.setItemAsync(KEY, t),
  clear: () => SecureStore.deleteItemAsync(KEY),
}
