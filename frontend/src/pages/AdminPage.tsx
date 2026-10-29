import { Badge, Card, Group, Loader, Select, Stack, Switch, Table, Tabs, Text, Title } from '@mantine/core'
import { useCallback, useEffect, useState } from 'react'
import { get, patch } from '../api'
import { useAuth } from '../auth'
import { formatDate } from '../format'
import { notifyError, notifySuccess } from '../notify'
import type { AdminUser, AuditEntry, Role } from '../types'

const ROLES: Role[] = ['Analyst', 'QA Engineer', 'Developer', 'Administrator']
const ACTION_COLOR: Record<string, string> = {
  create: 'teal',
  generate: 'blue',
  edit: 'yellow',
  approve: 'green',
  export: 'grape',
  delete: 'red',
  archive: 'gray',
}

function UsersPanel() {
  const { user: me } = useAuth()
  const [users, setUsers] = useState<AdminUser[] | null>(null)
  const load = useCallback(() => {
    get<AdminUser[]>('/admin/users').then(setUsers).catch(notifyError)
  }, [])
  useEffect(load, [load])

  async function update(user: AdminUser, change: Partial<Pick<AdminUser, 'role' | 'is_active'>>) {
    try {
      await patch(`/admin/users/${user.id}`, change)
      notifySuccess(`${user.name} updated`)
      load()
    } catch (err) {
      notifyError(err)
    }
  }

  if (!users) return <Loader />
  return (
    <Table striped>
      <Table.Thead>
        <Table.Tr>
          <Table.Th>Name</Table.Th>
          <Table.Th>Email</Table.Th>
          <Table.Th w={200}>Role</Table.Th>
          <Table.Th w={90}>Active</Table.Th>
          <Table.Th>Registered</Table.Th>
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>
        {users.map((u) => (
          <Table.Tr key={u.id}>
            <Table.Td>{u.name}</Table.Td>
            <Table.Td>{u.email}</Table.Td>
            <Table.Td>
              <Select
                size="xs"
                data={ROLES}
                value={u.role}
                allowDeselect={false}
                disabled={u.id === me?.id}
                onChange={(role) => role && role !== u.role && update(u, { role: role as Role })}
                aria-label={`Role of ${u.name}`}
              />
            </Table.Td>
            <Table.Td>
              <Switch
                checked={u.is_active}
                disabled={u.id === me?.id}
                onChange={(e) => update(u, { is_active: e.currentTarget.checked })}
                aria-label={`${u.name} active`}
              />
            </Table.Td>
            <Table.Td>{formatDate(u.created_at)}</Table.Td>
          </Table.Tr>
        ))}
      </Table.Tbody>
    </Table>
  )
}

function AuditPanel() {
  const [entries, setEntries] = useState<AuditEntry[] | null>(null)
  useEffect(() => {
    get<AuditEntry[]>('/admin/audit?limit=300').then(setEntries).catch(notifyError)
  }, [])
  if (!entries) return <Loader />
  return (
    <Table striped fz="sm">
      <Table.Thead>
        <Table.Tr>
          <Table.Th w={170}>When</Table.Th>
          <Table.Th>Who</Table.Th>
          <Table.Th>Action</Table.Th>
          <Table.Th>What</Table.Th>
          <Table.Th>Project</Table.Th>
          <Table.Th>Detail</Table.Th>
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>
        {entries.map((e) => (
          <Table.Tr key={e.id}>
            <Table.Td>{formatDate(e.created_at)}</Table.Td>
            <Table.Td>{e.user_name ?? '—'}</Table.Td>
            <Table.Td>
              <Badge color={ACTION_COLOR[e.action] ?? 'gray'} variant="light">
                {e.action}
              </Badge>
            </Table.Td>
            <Table.Td>
              {e.entity}
              {e.entity_id ? ` ${e.entity_id}` : ''}
            </Table.Td>
            <Table.Td>{e.project_name ?? ''}</Table.Td>
            <Table.Td>
              <Text size="xs" c="dimmed">
                {e.detail}
              </Text>
            </Table.Td>
          </Table.Tr>
        ))}
      </Table.Tbody>
    </Table>
  )
}

/** Administrator page: user roles and the audit log (FR-12, FR-15). */
export default function AdminPage() {
  return (
    <Stack>
      <Group>
        <Title order={2}>Administration</Title>
      </Group>
      <Card withBorder p={0}>
        <Tabs defaultValue="users" keepMounted={false}>
          <Tabs.List px="sm">
            <Tabs.Tab value="users">Users and roles</Tabs.Tab>
            <Tabs.Tab value="audit">Audit log</Tabs.Tab>
          </Tabs.List>
          <Tabs.Panel value="users" p="sm">
            <UsersPanel />
          </Tabs.Panel>
          <Tabs.Panel value="audit" p="sm">
            <AuditPanel />
          </Tabs.Panel>
        </Tabs>
      </Card>
    </Stack>
  )
}
