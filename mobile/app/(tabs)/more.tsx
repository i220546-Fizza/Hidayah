import { useAuth } from '@/auth/AuthContext'
import { Button, H2, P, RowLink, Screen } from '@/ui/kit'

export default function More() {
  const { status, user, logout } = useAuth()
  return (
    <Screen>
      <RowLink href="/learning" title="Learning" subtitle="Paths and quizzes" />
      <RowLink href="/search" title="Search" subtitle="Find words in approved sources" />
      <RowLink href="/sources" title="Sources and credits" subtitle="Where every text comes from" />
      <RowLink href="/about" title="About" />
      <H2>Account</H2>
      {status === 'authenticated' ? (
        <>
          <P>{user?.display_name || user?.email}</P>
          <RowLink href="/account" title="Your account" subtitle="Your questions, data and deletion" />
          <Button variant="secondary" title="Log out" onPress={() => void logout()} />
        </>
      ) : status === 'anonymous' ? (
        <>
          <RowLink href="/login" title="Log in" />
          <RowLink href="/register" title="Create account" />
        </>
      ) : null}
    </Screen>
  )
}
