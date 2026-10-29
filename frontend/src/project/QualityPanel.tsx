import { Alert, Badge, Card, CloseButton, Group, Stack, Table, Text, Title } from '@mantine/core'
import type { QualityReport } from '../types'

const KIND_COLOR: Record<string, string> = { vague: 'orange', missing: 'red', conflict: 'grape' }

/** Results of the ambiguity and completeness check (FR-11). */
export default function QualityPanel({ report, onClose }: { report: QualityReport; onClose: () => void }) {
  return (
    <Card withBorder>
      <Group justify="space-between" mb="sm">
        <Group gap="xs">
          <Title order={4}>Quality check</Title>
          <Badge color="orange" variant="light">
            {report.vague} vague
          </Badge>
          <Badge color="red" variant="light">
            {report.missing} missing
          </Badge>
          <Badge color="grape" variant="light">
            {report.conflicts} conflicts
          </Badge>
        </Group>
        <CloseButton aria-label="Close quality check" onClick={onClose} />
      </Group>
      {report.conflict_check === 'unavailable' && (
        <Alert color="yellow" mb="sm">
          The AI conflict check is unavailable right now; vague-wording and missing-section checks still ran.
        </Alert>
      )}
      {report.flags.length === 0 ? (
        <Text c="teal">No issues found.</Text>
      ) : (
        <Table verticalSpacing="xs">
          <Table.Thead>
            <Table.Tr>
              <Table.Th w={100}>Type</Table.Th>
              <Table.Th w={180}>Where</Table.Th>
              <Table.Th>Problem</Table.Th>
              <Table.Th>Suggested rewrite</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {report.flags.map((f, i) => (
              <Table.Tr key={i}>
                <Table.Td>
                  <Badge color={KIND_COLOR[f.kind]} variant="light">
                    {f.kind}
                  </Badge>
                </Table.Td>
                <Table.Td ff="monospace" fz="sm">
                  {f.location}
                </Table.Td>
                <Table.Td>
                  <Stack gap={0}>
                    {f.text && (
                      <Text size="sm" fw={600}>
                        “{f.text}”
                      </Text>
                    )}
                    <Text size="sm">{f.reason}</Text>
                  </Stack>
                </Table.Td>
                <Table.Td>
                  <Text size="sm" c="teal.7">
                    {f.suggestion}
                  </Text>
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      )}
    </Card>
  )
}
