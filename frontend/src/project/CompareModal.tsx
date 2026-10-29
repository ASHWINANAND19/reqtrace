import { Badge, Card, Code, Group, Loader, Modal, Select, Stack, Text, Title } from '@mantine/core'
import { useEffect, useState } from 'react'
import { get } from '../api'
import { notifyError } from '../notify'
import type { SrsCompare, SrsSummary } from '../types'

interface Props {
  projectId: number
  versions: SrsSummary[]
  opened: boolean
  onClose: () => void
}

const LINE_COLOR: Record<string, string> = { '+': 'teal', '-': 'red' }

/** Side-by-side comparison of two SRS versions (FR-05). */
export default function CompareModal({ projectId, versions, opened, onClose }: Props) {
  const options = versions.map((v) => ({ value: String(v.id), label: `v${v.version_no} (${v.status})` }))
  const [a, setA] = useState<string | null>(options[1]?.value ?? null)
  const [b, setB] = useState<string | null>(options[0]?.value ?? null)
  const [result, setResult] = useState<SrsCompare | null>(null)

  useEffect(() => {
    if (opened && a && b) {
      get<SrsCompare>(`/projects/${projectId}/srs/compare?a=${a}&b=${b}`).then(setResult).catch(notifyError)
    }
  }, [opened, projectId, a, b])

  const shown = result && String(result.a.id) === a && String(result.b.id) === b ? result : null
  const changedSections = shown?.sections.filter((s) => s.changed) ?? []

  return (
    <Modal opened={opened} onClose={onClose} title="Compare versions" size="xl">
      <Group mb="md">
        <Select label="Older" data={options} value={a} onChange={setA} allowDeselect={false} />
        <Select label="Newer" data={options} value={b} onChange={setB} allowDeselect={false} />
      </Group>
      {!shown && a && b && <Loader />}
      {shown && (
        <Stack>
          <Title order={5}>Requirements ({shown.requirements.length} changed)</Title>
          {shown.requirements.length === 0 && <Text c="dimmed">No requirement changes.</Text>}
          {shown.requirements.map((c) => (
            <Card key={c.req_id} withBorder p="xs">
              <Group gap="xs" mb={4}>
                <Code>{c.req_id}</Code>
                <Badge color={!c.before ? 'teal' : !c.after ? 'red' : 'blue'} variant="light">
                  {!c.before ? 'added' : !c.after ? 'removed' : 'changed'}
                </Badge>
              </Group>
              {c.before && c.after && c.before.description !== c.after.description ? (
                <>
                  <Text size="sm" c="red">
                    − {c.before.description}
                  </Text>
                  <Text size="sm" c="teal">
                    + {c.after.description}
                  </Text>
                </>
              ) : (
                <Text size="sm">{(c.after ?? c.before)?.description}</Text>
              )}
            </Card>
          ))}

          <Title order={5}>Sections ({changedSections.length} changed)</Title>
          {changedSections.length === 0 && <Text c="dimmed">No section changes.</Text>}
          {changedSections.map((s) => (
            <Card key={s.number} withBorder p="xs">
              <Text fw={600} size="sm" mb={4}>
                {s.number} {s.title}
              </Text>
              {s.lines.map((line, i) => (
                <Text key={i} size="sm" ff="monospace" c={LINE_COLOR[line[0]]} style={{ whiteSpace: 'pre-wrap' }}>
                  {line}
                </Text>
              ))}
            </Card>
          ))}
        </Stack>
      )}
    </Modal>
  )
}
