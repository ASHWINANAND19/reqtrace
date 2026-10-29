import { Alert, Anchor, Button, Center, Paper, PasswordInput, Stack, Text, TextInput, Title } from '@mantine/core'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      await login(email, password)
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Center mih="70vh">
      <Paper withBorder shadow="sm" p="xl" w={380} component="form" onSubmit={submit}>
        <Stack>
          <Title order={2}>Log in</Title>
          <Text size="sm" c="dimmed">
            Turn raw requirements into an SRS, tests and a traceability matrix.
          </Text>
          {error && <Alert color="red">{error}</Alert>}
          <TextInput label="Email" type="email" required value={email} onChange={(e) => setEmail(e.currentTarget.value)} />
          <PasswordInput label="Password" required value={password} onChange={(e) => setPassword(e.currentTarget.value)} />
          <Button type="submit" loading={busy}>
            Log in
          </Button>
          <Text size="sm">
            New here?{' '}
            <Anchor component={Link} to="/register">
              Create an account
            </Anchor>
          </Text>
        </Stack>
      </Paper>
    </Center>
  )
}
