import { ActionIcon, Badge, Button, Card, Group, Stack, Table, Text, TextInput, Title } from '@mantine/core'
import { modals } from '@mantine/modals'
import { IconArchive, IconTrash, IconUserMinus, IconUserPlus } from '@tabler/icons-react'
import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { del, patch, post } from '../api'
import { useAuth } from '../auth'
import { notifyError, notifySuccess } from '../notify'
import type { ProjectTabProps } from '../pages/ProjectPage'

export default function OverviewTab({ project, reload }: ProjectTabProps) {
  const { user, can } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [name, setName] = useState(project.name)
  const isOwner = user?.id === project.owner_id || can('Administrator')

  async function addMember(e: FormEvent) {
    e.preventDefault()
    try {
      await post(`/projects/${project.id}/members`, { email })
      setEmail('')
      notifySuccess('Member added')
      reload()
    } catch (err) {
      notifyError(err)
    }
  }

  async function run(action: () => Promise<unknown>, message: string) {
    try {
      await action()
      notifySuccess(message)
      reload()
    } catch (err) {
      notifyError(err)
    }
  }

  function confirmDelete() {
    modals.openConfirmModal({
      title: 'Delete project?',
      children: <Text size="sm">This permanently removes the project and all its artefacts.</Text>,
      labels: { confirm: 'Delete', cancel: 'Cancel' },
      confirmProps: { color: 'red' },
      onConfirm: async () => {
        try {
          await del(`/projects/${project.id}`)
          notifySuccess('Project deleted')
          navigate('/')
        } catch (err) {
          notifyError(err)
        }
      },
    })
  }

  return (
    <Stack>
      <Card withBorder>
        <Title order={4} mb="sm">
          Members
        </Title>
        <Table>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Name</Table.Th>
              <Table.Th>Email</Table.Th>
              <Table.Th>Role</Table.Th>
              <Table.Th />
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {project.members.map((m) => (
              <Table.Tr key={m.id}>
                <Table.Td>
                  {m.name} {m.id === project.owner_id && <Badge size="xs">owner</Badge>}
                </Table.Td>
                <Table.Td>{m.email}</Table.Td>
                <Table.Td>{m.role}</Table.Td>
                <Table.Td>
                  {isOwner && m.id !== project.owner_id && (
                    <ActionIcon
                      variant="subtle"
                      color="red"
                      aria-label={`Remove ${m.name}`}
                      onClick={() => run(() => del(`/projects/${project.id}/members/${m.id}`), 'Member removed')}
                    >
                      <IconUserMinus size={16} />
                    </ActionIcon>
                  )}
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
        {isOwner && (
          <Group component="form" onSubmit={addMember} mt="md" align="flex-end">
            <TextInput
              label="Add member by email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.currentTarget.value)}
              style={{ flex: 1 }}
            />
            <Button type="submit" leftSection={<IconUserPlus size={16} />}>
              Add
            </Button>
          </Group>
        )}
      </Card>

      {isOwner && (
        <Card withBorder>
          <Title order={4} mb="sm">
            Settings
          </Title>
          <Group align="flex-end">
            <TextInput label="Project name" value={name} onChange={(e) => setName(e.currentTarget.value)} style={{ flex: 1 }} />
            <Button variant="default" onClick={() => run(() => patch(`/projects/${project.id}`, { name }), 'Project renamed')}>
              Rename
            </Button>
          </Group>
          <Group mt="md">
            <Button
              variant="default"
              leftSection={<IconArchive size={16} />}
              onClick={() =>
                run(
                  () => patch(`/projects/${project.id}`, { archived: !project.archived }),
                  project.archived ? 'Project restored' : 'Project archived',
                )
              }
            >
              {project.archived ? 'Restore' : 'Archive'}
            </Button>
            <Button color="red" variant="light" leftSection={<IconTrash size={16} />} onClick={confirmDelete}>
              Delete project
            </Button>
          </Group>
        </Card>
      )}
    </Stack>
  )
}
