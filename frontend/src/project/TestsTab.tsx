import {
  ActionIcon,
  Alert,
  Badge,
  Button,
  Card,
  Group,
  List,
  Loader,
  Modal,
  MultiSelect,
  Select,
  Stack,
  Table,
  Text,
  TextInput,
  Textarea,
} from '@mantine/core'
import { IconPencil, IconPlus, IconSparkles, IconTrash } from '@tabler/icons-react'
import { useCallback, useEffect, useState } from 'react'
import { del, get, post, put } from '../api'
import { useAuth } from '../auth'
import { TYPE_COLOR } from '../format'
import { notifyError, notifySuccess } from '../notify'
import type { ProjectTabProps } from '../pages/ProjectPage'
import type { SrsVersion, TestCase, TestSuite } from '../types'

type Draft = Omit<TestCase, 'id' | 'tc_id' | 'created_at'>
const EMPTY: Draft = { title: '', type: 'positive', preconditions: '', steps: [''], expected_result: '', requirement_ids: [] }

export default function TestsTab({ project }: ProjectTabProps) {
  const { can } = useAuth()
  const canGenerate = can('QA Engineer', 'Analyst', 'Administrator')
  const [suite, setSuite] = useState<TestSuite | null>(null)
  const [reqIds, setReqIds] = useState<string[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [editing, setEditing] = useState<{ id: number | null; draft: Draft } | null>(null)
  const base = `/projects/${project.id}/tests`

  const load = useCallback(() => {
    get<TestSuite>(base)
      .then((s) => {
        setSuite(s)
        if (s.srs_version) {
          get<SrsVersion>(`/projects/${project.id}/srs/versions/${s.srs_version.id}`)
            .then((v) => setReqIds(v.requirements.map((r) => r.req_id)))
            .catch(notifyError)
        }
      })
      .catch(notifyError)
  }, [base, project.id])
  useEffect(load, [load])

  async function generate() {
    setBusy(true)
    setError('')
    try {
      const result = await post<TestSuite>(`${base}/generate`)
      setSuite(result)
      notifySuccess(`${result.test_cases.length} test cases generated`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Generation failed.')
    } finally {
      setBusy(false)
    }
  }

  async function save() {
    if (!editing) return
    const body = { ...editing.draft, steps: editing.draft.steps.filter((s) => s.trim()) }
    try {
      if (editing.id) await put(`${base}/${editing.id}`, body)
      else await post(base, body)
      setEditing(null)
      notifySuccess('Test case saved')
      load()
    } catch (err) {
      notifyError(err)
    }
  }

  async function remove(tc: TestCase) {
    try {
      await del(`${base}/${tc.id}`)
      notifySuccess(`${tc.tc_id} deleted`)
      load()
    } catch (err) {
      notifyError(err)
    }
  }

  if (!suite) return <Loader />
  const setDraft = (patch: Partial<Draft>) => setEditing((e) => (e ? { ...e, draft: { ...e.draft, ...patch } } : e))

  return (
    <Stack>
      <Card withBorder>
        <Group justify="space-between">
          <Text size="sm" c="dimmed">
            {suite.srs_version
              ? `Based on approved SRS v${suite.srs_version.version_no} · ${suite.test_cases.length} test cases`
              : 'Approve an SRS version on the SRS tab to generate tests.'}
          </Text>
          {canGenerate && (
            <Group>
              {suite.srs_version && (
                <Button variant="default" leftSection={<IconPlus size={16} />} onClick={() => setEditing({ id: null, draft: EMPTY })}>
                  Add test case
                </Button>
              )}
              <Button leftSection={<IconSparkles size={16} />} loading={busy} onClick={generate}>
                Generate tests
              </Button>
            </Group>
          )}
        </Group>
        {busy && (
          <Text size="sm" c="dimmed" mt="sm">
            The test case agent is writing positive, negative and boundary tests for each requirement…
          </Text>
        )}
        {error && (
          <Alert color="red" mt="sm">
            {error}
          </Alert>
        )}
      </Card>

      {suite.test_cases.length > 0 && (
        <Card withBorder p={0}>
          <Table striped verticalSpacing="sm">
            <Table.Thead>
              <Table.Tr>
                <Table.Th w={80}>ID</Table.Th>
                <Table.Th w={110}>Requirement</Table.Th>
                <Table.Th w={100}>Type</Table.Th>
                <Table.Th>Title and steps</Table.Th>
                <Table.Th>Expected result</Table.Th>
                {canGenerate && <Table.Th w={70} />}
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {suite.test_cases.map((tc) => (
                <Table.Tr key={tc.id}>
                  <Table.Td ff="monospace">{tc.tc_id}</Table.Td>
                  <Table.Td ff="monospace">{tc.requirement_ids.join(', ')}</Table.Td>
                  <Table.Td>
                    <Badge color={TYPE_COLOR[tc.type]} variant="light">
                      {tc.type}
                    </Badge>
                  </Table.Td>
                  <Table.Td>
                    <Text fw={500} size="sm">
                      {tc.title}
                    </Text>
                    <List type="ordered" size="xs" mt={4}>
                      {tc.steps.map((step, i) => (
                        <List.Item key={i}>{step}</List.Item>
                      ))}
                    </List>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm">{tc.expected_result}</Text>
                  </Table.Td>
                  {canGenerate && (
                    <Table.Td>
                      <Group gap={4} wrap="nowrap">
                        <ActionIcon variant="subtle" aria-label={`Edit ${tc.tc_id}`} onClick={() => setEditing({ id: tc.id, draft: { ...tc } })}>
                          <IconPencil size={16} />
                        </ActionIcon>
                        <ActionIcon variant="subtle" color="red" aria-label={`Delete ${tc.tc_id}`} onClick={() => remove(tc)}>
                          <IconTrash size={16} />
                        </ActionIcon>
                      </Group>
                    </Table.Td>
                  )}
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        </Card>
      )}

      <Modal opened={!!editing} onClose={() => setEditing(null)} title={editing?.id ? 'Edit test case' : 'New test case'} size="lg">
        {editing && (
          <Stack>
            <TextInput label="Title" value={editing.draft.title} onChange={(e) => setDraft({ title: e.currentTarget.value })} />
            <Group grow>
              <Select
                label="Type"
                data={['positive', 'negative', 'boundary']}
                value={editing.draft.type}
                allowDeselect={false}
                onChange={(v) => setDraft({ type: v as TestCase['type'] })}
              />
              <MultiSelect
                label="Requirements"
                data={reqIds}
                value={editing.draft.requirement_ids}
                onChange={(v) => setDraft({ requirement_ids: v })}
                searchable
              />
            </Group>
            <Textarea label="Preconditions" autosize value={editing.draft.preconditions} onChange={(e) => setDraft({ preconditions: e.currentTarget.value })} />
            <Textarea
              label="Steps (one per line)"
              autosize
              minRows={3}
              value={editing.draft.steps.join('\n')}
              onChange={(e) => setDraft({ steps: e.currentTarget.value.split('\n') })}
            />
            <Textarea label="Expected result" autosize value={editing.draft.expected_result} onChange={(e) => setDraft({ expected_result: e.currentTarget.value })} />
            <Button onClick={save}>Save</Button>
          </Stack>
        )}
      </Modal>
    </Stack>
  )
}
