import { Alert, Badge, Card, Group, Loader, Progress, SimpleGrid, Stack, Table, Text, Title } from '@mantine/core'
import { IconAlertTriangle } from '@tabler/icons-react'
import { useEffect, useState } from 'react'
import { get } from '../api'
import { PRIORITY_COLOR } from '../format'
import { notifyError } from '../notify'
import type { ProjectTabProps } from '../pages/ProjectPage'
import type { TraceMatrix } from '../types'

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <Card withBorder>
      <Text size="xs" c="dimmed" tt="uppercase">
        {label}
      </Text>
      <Text fz={28} fw={600}>
        {value}
      </Text>
    </Card>
  )
}

/** Requirement-to-test matrix with coverage; uncovered requirements are highlighted (FR-07). */
export default function TraceabilityTab({ project }: ProjectTabProps) {
  const [matrix, setMatrix] = useState<TraceMatrix | null>(null)

  useEffect(() => {
    get<TraceMatrix>(`/projects/${project.id}/traceability`).then(setMatrix).catch(notifyError)
  }, [project.id])

  if (!matrix) return <Loader />
  if (!matrix.srs_version) return <Text c="dimmed">Approve an SRS version and generate tests to see the matrix.</Text>

  const color = matrix.coverage_percent === 100 ? 'teal' : matrix.coverage_percent >= 80 ? 'yellow' : 'red'
  return (
    <Stack>
      <SimpleGrid cols={{ base: 1, sm: 3 }}>
        <Stat label="Coverage" value={`${matrix.coverage_percent}%`} />
        <Stat label="Requirements covered" value={`${matrix.covered} / ${matrix.total}`} />
        <Stat label="Uncovered" value={matrix.uncovered.length} />
      </SimpleGrid>
      <Progress value={matrix.coverage_percent} color={color} size="lg" aria-label="Coverage" />
      {matrix.uncovered.length > 0 && (
        <Alert color="red" icon={<IconAlertTriangle size={18} />}>
          No test cases for: {matrix.uncovered.join(', ')}
        </Alert>
      )}
      <Card withBorder p={0}>
        <Group p="sm">
          <Title order={5}>Traceability matrix · SRS v{matrix.srs_version.version_no}</Title>
        </Group>
        <Table verticalSpacing="xs">
          <Table.Thead>
            <Table.Tr>
              <Table.Th w={100}>Requirement</Table.Th>
              <Table.Th>Title</Table.Th>
              <Table.Th w={90}>Priority</Table.Th>
              <Table.Th>Test cases</Table.Th>
              <Table.Th w={70}>Count</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {matrix.rows.map((r) => (
              <Table.Tr key={r.req_id} bg={r.covered ? undefined : 'var(--mantine-color-red-light)'}>
                <Table.Td ff="monospace">{r.req_id}</Table.Td>
                <Table.Td>{r.title}</Table.Td>
                <Table.Td>
                  <Badge color={PRIORITY_COLOR[r.priority] ?? 'gray'} variant="light">
                    {r.priority}
                  </Badge>
                </Table.Td>
                <Table.Td>
                  {r.covered ? (
                    <Group gap={4}>
                      {r.test_cases.map((tc) => (
                        <Badge key={tc} variant="outline" ff="monospace">
                          {tc}
                        </Badge>
                      ))}
                    </Group>
                  ) : (
                    <Text c="red" size="sm" fw={500}>
                      Not covered
                    </Text>
                  )}
                </Table.Td>
                <Table.Td>{r.test_cases.length}</Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      </Card>
    </Stack>
  )
}
