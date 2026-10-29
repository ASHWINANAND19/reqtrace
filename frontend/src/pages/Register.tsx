import { Alert, Anchor, Button, Center, Paper, PasswordInput, Select, Stack, Text, TextInput, Title } from '@mantine/core'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { post } from '../api'
import { useAuth } from '../auth'

const ROLES = ['Analyst', 'QA Engineer', 'Developer']

export default function Register() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'Analyst' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const set = (key: keyof typeof form) => (value: string) => setForm((f) => ({ ...f, [key]: value }))

  async function submit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      await post('/auth/register', form)
      await login(form.email, form.password)
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Center mih="70vh">
      <Paper withBorder shadow="sm" p="xl" w={400} component="form" onSubmit={submit}>
        <Stack>
          <Title order={2}>Create an account</Title>
          {error && <Alert color="red">{error}</Alert>}
          <TextInput label="Name" required value={form.name} onChange={(e) => set('name')(e.currentTarget.value)} />
          <TextInput
            label="Email"
            type="email"
            required
            value={form.email}
            onChange={(e) => set('email')(e.currentTarget.value)}
          />
          <PasswordInput
            label="Password"
            description="At least 8 characters"
            required
            value={form.password}
            onChange={(e) => set('password')(e.currentTarget.value)}
          />
          <Select label="Role" data={ROLES} value={form.role} onChange={(v) => set('role')(v ?? 'Analyst')} allowDeselect={false} />
          <Button type="submit" loading={busy}>
            Create account
          </Button>
          <Text size="sm">
            Already registered?{' '}
            <Anchor component={Link} to="/login">
              Log in
            </Anchor>
          </Text>
        </Stack>
      </Paper>
    </Center>
  )
}
