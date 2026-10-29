import {
  Alert,
  Badge,
  Button,
  Card,
  Group,
  Loader,
  Modal,
  SimpleGrid,
  Stack,
  Switch,
  Text,
  TextInput,
  Textarea,
  Title,
} from '@mantine/core'
import { IconPlus, IconUsers } from '@tabler/icons-react'
import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { get, post } from '../api'
import type { Project, ProjectDetail } from '../types'

export default function Dashboard() {
  const navigate = useNavigate()
  const [projects, setProjects] = useState<Project[] | null>(null)
  const [showArchived, setShowArchived] = useState(false)
  const [error, setError] = useState('')
  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [formError, setFormError] = useState('')
  const [busy, setBusy] = useState(false)

  const load = useCallback(() => {
    get<Project[]>(`/projects?include_archived=${showArchived}`)
      .then(setProjects)
      .catch((err) => setError(err.message))
  }, [showArchived])

  useEffect(load, [load])

  async function create(e: FormEvent) {
    e.preventDefault()
    setFormError('')
    setBusy(true)
    try {
      const project = await post<ProjectDetail>('/projects', { name, description })
      navigate(`/projects/${project.id}`)
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Could not create project.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={2}>Projects</Title>
        <Group>
          <Switch label="Show archived" checked={showArchived} onChange={(e) => setShowArchived(e.currentTarget.checked)} />
          <Button leftSection={<IconPlus size={16} />} onClick={() => setOpen(true)}>
            New project
          </Button>
        </Group>
      </Group>

      {error && <Alert color="red">{error}</Alert>}
      {projects === null && !error && <Loader />}
      {projects?.length === 0 && (
        <Card withBorder p="xl">
          <Text c="dimmed">No projects yet. Create one to start capturing requirements.</Text>
        </Card>
      )}

      <SimpleGrid cols={{ base: 1, sm: 2, lg: 3 }}>
        {projects?.map((p) => (
          <Card key={p.id} withBorder shadow="xs" component={Link} to={`/projects/${p.id}`}>
            <Group justify="space-between" mb="xs" wrap="nowrap">
              <Text fw={600} truncate>
                {p.name}
              </Text>
              {p.archived && <Badge color="gray">Archived</Badge>}
            </Group>
            <Text size="sm" c="dimmed" lineClamp={2} mih={40}>
              {p.description || 'No description'}
            </Text>
            <Group gap="xs" mt="sm">
              <IconUsers size={14} />
              <Text size="xs" c="dimmed">
                {p.member_count} member{p.member_count === 1 ? '' : 's'} · owner {p.owner_name}
              </Text>
            </Group>
          </Card>
        ))}
      </SimpleGrid>

      <Modal opened={open} onClose={() => setOpen(false)} title="New project">
        <Stack component="form" onSubmit={create}>
          {formError && <Alert color="red">{formError}</Alert>}
          <TextInput label="Name" required value={name} onChange={(e) => setName(e.currentTarget.value)} data-autofocus />
          <Textarea label="Description" autosize minRows={2} value={description} onChange={(e) => setDescription(e.currentTarget.value)} />
          <Button type="submit" loading={busy}>
            Create
          </Button>
        </Stack>
      </Modal>
    </Stack>
  )
}
