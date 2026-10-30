import { ActionIcon, Button, Card, Group, Select, Stack, Table, Text, TextInput, Textarea, Title } from '@mantine/core'
import { IconPlus, IconTrash } from '@tabler/icons-react'
import { useState } from 'react'
import { post } from '../api'
import { notifyError, notifySuccess } from '../notify'
import type { SrsRequirement, SrsVersion } from '../types'

interface Props {
  projectId: number
  version: SrsVersion
  onSaved: (saved: SrsVersion) => void
  onCancel: () => void
}

function nextId(rows: SrsRequirement[], type: SrsRequirement['type']) {
  const prefix = type === 'functional' ? 'FR' : 'NFR'
  const used = rows
    .map((r) => new RegExp(`^${prefix}-(\\d+)$`).exec(r.req_id)?.[1])
    .filter(Boolean)
    .map(Number)
  return `${prefix}-${String(Math.max(0, ...used) + 1).padStart(2, '0')}`
}

/** Edit an SRS version; saving always creates a new version (FR-05). */
export default function SrsEditor({ projectId, version, onSaved, onCancel }: Props) {
  const [title, setTitle] = useState(version.title)
  const [sections, setSections] = useState(version.sections)
  const [rows, setRows] = useState(version.requirements)
  const [note, setNote] = useState('')
  const [saving, setSaving] = useState(false)

  const setSection = (number: string, content: string) =>
    setSections((all) => all.map((s) => (s.number === number ? { ...s, content } : s)))
  const setRow = (index: number, patch: Partial<SrsRequirement>) =>
    setRows((all) => all.map((r, i) => (i === index ? { ...r, ...patch } : r)))
  const addRow = (type: SrsRequirement['type']) =>
    setRows((all) => [
      ...all,
      { req_id: nextId(all, type), type, title: '', description: 'The system shall ', priority: 'Should' },
    ])

  async function save() {
    setSaving(true)
    try {
      const saved = await post<SrsVersion>(`/projects/${projectId}/srs/versions`, {
        base_version_id: version.id,
        title,
        sections: sections.map(({ number, content }) => ({ number, content })),
        requirements: rows,
        note,
      })
      notifySuccess(`Saved as version ${saved.version_no}`)
      onSaved(saved)
    } catch (err) {
      notifyError(err)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Stack>
      <Card withBorder>
        <Group justify="space-between" align="flex-end">
          <TextInput label="Document title" value={title} onChange={(e) => setTitle(e.currentTarget.value)} style={{ flex: 1 }} />
          <TextInput
            label="Change note"
            placeholder={`Edited from v${version.version_no}`}
            value={note}
            onChange={(e) => setNote(e.currentTarget.value)}
            w={280}
          />
          <Button variant="default" onClick={onCancel}>
            Cancel
          </Button>
          <Button loading={saving} onClick={save}>
            Save as new version
          </Button>
        </Group>
      </Card>

      <Card withBorder>
        <Title order={4} mb="sm">
          Sections
        </Title>
        <Stack>
          {sections.map((s) => (
            <Textarea
              key={s.number}
              label={`${s.number} ${s.title}`}
              autosize
              minRows={2}
              maxRows={10}
              value={s.content}
              onChange={(e) => setSection(s.number, e.currentTarget.value)}
            />
          ))}
        </Stack>
      </Card>

      <Card withBorder>
        <Group justify="space-between" mb="sm">
          <Title order={4}>Requirements</Title>
          <Group>
            <Button size="xs" variant="light" leftSection={<IconPlus size={14} />} onClick={() => addRow('functional')}>
              Functional
            </Button>
            <Button size="xs" variant="light" leftSection={<IconPlus size={14} />} onClick={() => addRow('non-functional')}>
              Non-functional
            </Button>
          </Group>
        </Group>
        <Table>
          <Table.Thead>
            <Table.Tr>
              <Table.Th w={100}>ID</Table.Th>
              <Table.Th w={150}>Type</Table.Th>
              <Table.Th w={200}>Title</Table.Th>
              <Table.Th>Requirement</Table.Th>
              <Table.Th w={110}>Priority</Table.Th>
              <Table.Th w={40} />
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {rows.map((r, i) => (
              <Table.Tr key={i}>
                <Table.Td>
                  <TextInput size="xs" value={r.req_id} onChange={(e) => setRow(i, { req_id: e.currentTarget.value })} />
                </Table.Td>
                <Table.Td>
                  <Select
                    size="xs"
                    data={['functional', 'non-functional']}
                    value={r.type}
                    allowDeselect={false}
                    onChange={(v) => setRow(i, { type: v as SrsRequirement['type'] })}
                  />
                </Table.Td>
                <Table.Td>
                  <TextInput size="xs" value={r.title} onChange={(e) => setRow(i, { title: e.currentTarget.value })} />
                </Table.Td>
                <Table.Td>
                  <Textarea
                    size="xs"
                    autosize
                    minRows={1}
                    value={r.description}
                    onChange={(e) => setRow(i, { description: e.currentTarget.value })}
                  />
                </Table.Td>
                <Table.Td>
                  <Select
                    size="xs"
                    data={['Must', 'Should', 'Could']}
                    value={r.priority}
                    allowDeselect={false}
                    onChange={(v) => setRow(i, { priority: v as SrsRequirement['priority'] })}
                  />
                </Table.Td>
                <Table.Td>
                  <ActionIcon
                    variant="subtle"
                    color="red"
                    aria-label={`Delete ${r.req_id}`}
                    onClick={() => setRows((all) => all.filter((_, j) => j !== i))}
                  >
                    <IconTrash size={14} />
                  </ActionIcon>
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
        {rows.length === 0 && (
          <Text c="dimmed" size="sm" mt="sm">
            No requirements.
          </Text>
        )}
      </Card>
    </Stack>
  )
}
