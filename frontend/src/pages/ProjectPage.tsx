import { Alert, Badge, Group, Loader, Stack, Tabs, Text, Title } from '@mantine/core'
import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { get } from '../api'
import InputTab from '../project/InputTab'
import OverviewTab from '../project/OverviewTab'
import SrsTab from '../project/SrsTab'
import TestPlanTab from '../project/TestPlanTab'
import TestsTab from '../project/TestsTab'
import TraceabilityTab from '../project/TraceabilityTab'
import type { ProjectDetail } from '../types'

export interface ProjectTabProps {
  project: ProjectDetail
  reload: () => void
}

const TABS: { value: string; label: string; Component: (props: ProjectTabProps) => React.ReactNode }[] = [
  { value: 'overview', label: 'Overview', Component: OverviewTab },
  { value: 'input', label: 'Input', Component: InputTab },
  { value: 'srs', label: 'SRS', Component: SrsTab },
  { value: 'tests', label: 'Test Cases', Component: TestsTab },
  { value: 'traceability', label: 'Traceability', Component: TraceabilityTab },
  { value: 'test-plan', label: 'Test Plan', Component: TestPlanTab },
]

export default function ProjectPage() {
  const { id, tab = 'overview' } = useParams()
  const navigate = useNavigate()
  const [project, setProject] = useState<ProjectDetail | null>(null)
  const [error, setError] = useState('')

  const reload = useCallback(() => {
    get<ProjectDetail>(`/projects/${id}`)
      .then(setProject)
      .catch((err) => setError(err.message))
  }, [id])

  useEffect(reload, [reload])

  if (error) return <Alert color="red">{error}</Alert>
  if (!project) return <Loader />

  return (
    <Stack>
      <Group justify="space-between">
        <div>
          <Group gap="xs">
            <Title order={2}>{project.name}</Title>
            {project.archived && <Badge color="gray">Archived</Badge>}
          </Group>
          <Text size="sm" c="dimmed">
            {project.description || 'No description'}
          </Text>
        </div>
      </Group>
      <Tabs value={tab} onChange={(value) => navigate(`/projects/${id}/${value}`)} keepMounted={false}>
        <Tabs.List>
          {TABS.map((t) => (
            <Tabs.Tab key={t.value} value={t.value}>
              {t.label}
            </Tabs.Tab>
          ))}
        </Tabs.List>
        {TABS.map(({ value, Component }) => (
          <Tabs.Panel key={value} value={value} pt="md">
            <Component project={project} reload={reload} />
          </Tabs.Panel>
        ))}
      </Tabs>
    </Stack>
  )
}
