import { Link, type Href } from 'expo-router'
import type { ReactNode } from 'react'
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, TextInput, View, type TextInputProps } from 'react-native'
import { useSafeAreaInsets } from 'react-native-safe-area-context'
import type { UseQueryResult } from '@tanstack/react-query'
import { ApiError } from '@/lib/api'
import type { Source } from '@/lib/types'
import { colors, fonts, minTouchTarget, radius, spacing } from '@/theme/tokens'

export function Screen({ children }: { children: ReactNode }) {
  const insets = useSafeAreaInsets()
  return (
    <ScrollView style={{ backgroundColor: colors.ivory }} contentContainerStyle={{ padding: spacing.md, paddingBottom: insets.bottom + spacing.xl, gap: spacing.md }}>
      {children}
    </ScrollView>
  )
}

export const H1 = ({ children }: { children: ReactNode }) => <Text accessibilityRole="header" style={s.h1}>{children}</Text>
export const H2 = ({ children }: { children: ReactNode }) => <Text accessibilityRole="header" style={s.h2}>{children}</Text>
export const P = ({ children, small }: { children: ReactNode; small?: boolean }) => <Text style={small ? s.small : s.p}>{children}</Text>

export function Card({ children }: { children: ReactNode }) {
  return <View style={s.card}>{children}</View>
}

export function Arabic({ children, size = 28 }: { children: ReactNode; size?: number }) {
  return <Text style={{ fontFamily: fonts.arabic, fontSize: size, lineHeight: size * 1.9, color: colors.emerald, textAlign: 'right', writingDirection: 'rtl' }}>{children}</Text>
}

export function Button({ title, onPress, disabled, variant = 'primary' }: { title: string; onPress: () => void; disabled?: boolean; variant?: 'primary' | 'secondary' }) {
  const primary = variant === 'primary'
  return (
    <Pressable accessibilityRole="button" accessibilityState={{ disabled: !!disabled }} disabled={disabled} onPress={onPress}
      style={[s.btn, primary ? s.btnPrimary : s.btnSecondary, disabled && { opacity: 0.5 }]}>
      <Text style={{ fontFamily: fonts.sansMedium, color: primary ? colors.ivory : colors.emerald }}>{title}</Text>
    </Pressable>
  )
}

export function RowLink({ href, title, subtitle, right }: { href: Href; title: string; subtitle?: string; right?: ReactNode }) {
  return (
    <Link href={href} asChild>
      <Pressable accessibilityRole="link" style={s.row}>
        <View style={{ flex: 1 }}>
          <Text style={s.rowTitle}>{title}</Text>
          {subtitle ? <Text style={s.small}>{subtitle}</Text> : null}
        </View>
        {right}
      </Pressable>
    </Link>
  )
}

export function Field(props: TextInputProps & { label: string; error?: string }) {
  const { label, error, style, ...rest } = props
  return (
    <View>
      <Text style={s.label}>{label}</Text>
      <TextInput accessibilityLabel={label} placeholderTextColor={colors.charcoal} style={[s.input, error ? { borderColor: colors.terracotta } : null, style]} {...rest} />
      {error ? <Text accessibilityRole="alert" style={s.error}>{error}</Text> : null}
    </View>
  )
}

export function ErrorNote({ message }: { message: string }) {
  return <Text accessibilityRole="alert" style={[s.error, { padding: spacing.sm }]}>{message}</Text>
}

export function Empty({ title, children }: { title: string; children: ReactNode }) {
  return (
    <View style={s.empty}>
      <Text style={s.emptyTitle}>{title}</Text>
      <Text style={s.p}>{children}</Text>
    </View>
  )
}

export function SourceCredit({ source, label }: { source: Source | null; label?: string }) {
  if (!source) return null
  const parts = [source.title, source.edition, source.translator ? `tr. ${source.translator}` : null].filter(Boolean).join(' · ')
  const credit = source.attribution_text ?? source.rights_holder
  return <Text style={s.small}>{label ? `${label}: ` : 'Source: '}{parts}{credit ? ` — ${credit}` : ''}{source.license_name ? ` (${source.license_name})` : ''}</Text>
}

/** Loading and error states for a query. */
export function Async<T>({ query, children }: { query: UseQueryResult<T>; children: (d: T) => ReactNode }) {
  if (query.isPending) return <ActivityIndicator accessibilityLabel="Loading" color={colors.emerald} />
  if (query.isError) {
    const msg = query.error instanceof ApiError ? query.error.message : 'Something went wrong.'
    return (
      <View>
        <ErrorNote message={msg} />
        <Button variant="secondary" title="Try again" onPress={() => void query.refetch()} />
      </View>
    )
  }
  return <>{children(query.data)}</>
}

const s = StyleSheet.create({
  h1: { fontFamily: fonts.display, fontSize: 28, color: colors.charcoal },
  h2: { fontFamily: fonts.display, fontSize: 20, color: colors.emerald },
  p: { fontFamily: fonts.sans, fontSize: 16, lineHeight: 24, color: colors.charcoal },
  small: { fontFamily: fonts.sans, fontSize: 13, lineHeight: 19, color: colors.charcoal, opacity: 0.85 },
  card: { backgroundColor: colors.white, borderColor: colors.sand, borderWidth: 1, borderRadius: radius.md, padding: spacing.md, gap: spacing.sm },
  btn: { minHeight: minTouchTarget, borderRadius: radius.md, paddingHorizontal: spacing.lg, alignItems: 'center', justifyContent: 'center' },
  btnPrimary: { backgroundColor: colors.emerald },
  btnSecondary: { backgroundColor: colors.white, borderColor: colors.sage, borderWidth: 1 },
  row: { minHeight: minTouchTarget, flexDirection: 'row', alignItems: 'center', gap: spacing.md, backgroundColor: colors.white, borderColor: colors.sand, borderWidth: 1, borderRadius: radius.md, padding: spacing.md },
  rowTitle: { fontFamily: fonts.display, fontSize: 18, color: colors.emerald },
  label: { fontFamily: fonts.sansMedium, fontSize: 14, color: colors.charcoal, marginBottom: 6 },
  input: { minHeight: minTouchTarget, borderRadius: radius.md, borderWidth: 1, borderColor: colors.sage, backgroundColor: colors.white, paddingHorizontal: spacing.md, fontFamily: fonts.sans, fontSize: 16, color: colors.charcoal },
  error: { fontFamily: fonts.sansMedium, fontSize: 13, color: colors.terracottaDeep, marginTop: 4 },
  empty: { borderStyle: 'dashed', borderColor: colors.sage, borderWidth: 1, borderRadius: radius.md, padding: spacing.md, gap: 6 },
  emptyTitle: { fontFamily: fonts.display, fontSize: 18, color: colors.emerald },
})
