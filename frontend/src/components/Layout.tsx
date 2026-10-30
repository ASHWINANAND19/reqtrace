import { AppShell, Badge, Button, Container, Group, Text, Title } from '@mantine/core'
import { IconFileCheck, IconLogout, IconShieldLock } from '@tabler/icons-react'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../auth'

export default function Layout({ children }: { children: ReactNode }) {
  const { user, logout, can } = useAuth()
  return (
    <AppShell header={{ height: 60 }} footer={{ height: 36 }} padding="md">
      <AppShell.Header>
        <Container size="xl" h="100%">
          <Group h="100%" justify="space-between" wrap="nowrap">
            <Link to="/" style={{ textDecoration: 'none', color: 'inherit' }}>
              <Group gap="xs" wrap="nowrap">
                <IconFileCheck size={26} stroke={1.8} />
                <Title order={3}>ReqTrace</Title>
              </Group>
            </Link>
            {user && (
              <Group gap="sm" wrap="nowrap">
                {can('Administrator') && (
                  <Button component={Link} to="/admin" variant="subtle" leftSection={<IconShieldLock size={16} />}>
                    Admin
                  </Button>
                )}
                <Text size="sm" visibleFrom="sm">
                  {user.name}
                </Text>
                <Badge variant="light">{user.role}</Badge>
                <Button variant="default" size="xs" leftSection={<IconLogout size={14} />} onClick={logout}>
                  Log out
                </Button>
              </Group>
            )}
          </Group>
        </Container>
      </AppShell.Header>
      <AppShell.Main>
        <Container size="xl">{children}</Container>
      </AppShell.Main>
      <AppShell.Footer>
        <Container size="xl" h="100%">
          <Group h="100%">
            <Text size="xs" c="dimmed">
              AI-generated content must be reviewed by a human before use.
            </Text>
          </Group>
        </Container>
      </AppShell.Footer>
    </AppShell>
  )
}
