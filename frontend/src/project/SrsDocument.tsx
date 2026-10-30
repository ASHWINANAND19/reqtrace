import { Badge, Stack, Table, Text, Title } from '@mantine/core'
import { PRIORITY_COLOR } from '../format'
import type { SrsRequirement, SrsVersion } from '../types'

const CHAPTERS: Record<string, string> = {
  '1': '1. Introduction',
  '2': '2. Overall Description',
  '3': '3. Specific Requirements',
}

export function RequirementTable({ rows }: { rows: SrsRequirement[] }) {
  if (rows.length === 0) return <Text c="dimmed">None.</Text>
  return (
    <Table striped withTableBorder>
      <Table.Thead>
        <Table.Tr>
          <Table.Th w={90}>ID</Table.Th>
          <Table.Th w={200}>Title</Table.Th>
          <Table.Th>Requirement</Table.Th>
          <Table.Th w={90}>Priority</Table.Th>
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>
        {rows.map((r) => (
          <Table.Tr key={r.req_id}>
            <Table.Td>
              <Text ff="monospace" size="sm">
                {r.req_id}
              </Text>
            </Table.Td>
            <Table.Td>{r.title}</Table.Td>
            <Table.Td>{r.description}</Table.Td>
            <Table.Td>
              <Badge color={PRIORITY_COLOR[r.priority] ?? 'gray'} variant="light">
                {r.priority}
              </Badge>
            </Table.Td>
          </Table.Tr>
        ))}
      </Table.Tbody>
    </Table>
  )
}

/** Read-only IEEE 830 view of one SRS version. */
export default function SrsDocument({ version }: { version: SrsVersion }) {
  const functional = version.requirements.filter((r) => r.type === 'functional')
  const nonFunctional = version.requirements.filter((r) => r.type !== 'functional')
  const chapterOf = (number: string) => number.split('.')[0]
  return (
    <Stack gap="sm">
      <Title order={3}>{version.title}</Title>
      {version.sections.map((s, i) => {
        const startsChapter = i === 0 || chapterOf(version.sections[i - 1].number) !== chapterOf(s.number)
        const heading = startsChapter ? CHAPTERS[chapterOf(s.number)] : null
        return (
          <div key={s.number}>
            {heading && (
              <Title order={4} mt="md">
                {heading}
              </Title>
            )}
            <Text fw={600} mt="xs">
              {s.number} {s.title}
            </Text>
            <Text size="sm" style={{ whiteSpace: 'pre-wrap' }}>
              {s.content}
            </Text>
          </div>
        )
      })}
      <Text fw={600} mt="xs">
        3.2 Functional Requirements
      </Text>
      <RequirementTable rows={functional} />
      <Text fw={600} mt="xs">
        3.3 Non-Functional Requirements
      </Text>
      <RequirementTable rows={nonFunctional} />
    </Stack>
  )
}
