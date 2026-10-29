import { Alert, Badge, Button, Card, Group, Loader, Stack, Text, Textarea, Title } from '@mantine/core'
import { IconDeviceFloppy, IconPencil, IconSparkles } from '@tabler/icons-react'
import { useEffect, useState } from 'react'
import { get, post, put } from '../api'
import { useAuth } from '../auth'
import ExportButton from '../components/ExportButton'
import { formatDate } from '../format'
import { notifyError, notifySuccess } from '../notify'
import type { ProjectTabProps } from '../pages/ProjectPage'
import type { TestPlan } from '../types'

/** Generate, read and edit the test plan for the approved SRS (FR-09). */
export default function TestPlanTab({ project }: ProjectTabProps) {
  const { can } = useAuth()
  const canEdit = can('QA Engineer', 'Analyst', 'Administrator')
  const [plan, setPlan] = useState<TestPlan | null | undefined>(undefined)
  const [draft, setDraft] = useState<TestPlan['sections'] | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const base = `/projects/${project.id}/test-plan`

  useEffect(() => {
    get<TestPlan | null>(base).then(setPlan).catch(notifyError)
  }, [base])

  async function generate() {
    setBusy(true)
    setError('')
    try {
      setPlan(await post<TestPlan>(`${base}/generate`))
      notifySuccess('Test plan generated')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Generation failed.')
    } finally {
      setBusy(false)
    }
  }

  async function save() {
    if (!plan || !draft) return
    try {
      setPlan(await put<TestPlan>(`${base}/${plan.id}`, { sections: draft }))
      setDraft(null)
      notifySuccess('Test plan saved')
    } catch (err) {
      notifyError(err)
    }
  }

  if (plan === undefined) return <Loader />

  return (
    <Stack>
      <Card withBorder>
        <Group justify="space-between">
          <Text size="sm" c="dimmed">
            {plan
              ? `Based on approved SRS v${plan.srs_version_no} · updated ${formatDate(plan.updated_at)}`
              : 'No test plan yet.'}
          </Text>
          <Group>
            {plan && !draft && (
              <ExportButton
                path={`${base.replace('/test-plan', '/export')}/test-plan.docx`}
                fileName="test-plan.docx"
                label="Export DOCX"
              />
            )}
            {canEdit && (
              <Group>
                {plan && !draft && (
                  <Button
                    variant="default"
                    leftSection={<IconPencil size={16} />}
                    onClick={() => setDraft(plan.sections)}
                  >
                    Edit
                  </Button>
                )}
                {draft && (
                  <>
                    <Button variant="default" onClick={() => setDraft(null)}>
                      Cancel
                    </Button>
                    <Button leftSection={<IconDeviceFloppy size={16} />} onClick={save}>
                      Save
                    </Button>
                  </>
                )}
                {!draft && (
                  <Button leftSection={<IconSparkles size={16} />} loading={busy} onClick={generate}>
                    Generate test plan
                  </Button>
                )}
              </Group>
            )}
          </Group>
        </Group>
        {error && (
          <Alert color="red" mt="sm">
            {error}
          </Alert>
        )}
      </Card>

      {plan && (
        <Card withBorder>
          <Stack gap="md">
            <Title order={3}>Test Plan</Title>
            <Group gap={4}>
              <Text size="sm" fw={500}>
                Requirements in scope:
              </Text>
              {plan.requirement_ids.map((id) => (
                <Badge key={id} variant="outline" ff="monospace">
                  {id}
                </Badge>
              ))}
            </Group>
            {(draft ?? plan.sections).map((s, i) => (
              <div key={s.title}>
                <Title order={5}>
                  {i + 1}. {s.title}
                </Title>
                {draft ? (
                  <Textarea
                    autosize
                    minRows={2}
                    value={s.content}
                    onChange={(e) => {
                      const content = e.currentTarget.value
                      setDraft((d) => d && d.map((x, j) => (j === i ? { ...x, content } : x)))
                    }}
                  />
                ) : (
                  <Text size="sm" style={{ whiteSpace: 'pre-wrap' }}>
                    {s.content}
                  </Text>
                )}
              </div>
            ))}
          </Stack>
        </Card>
      )}
    </Stack>
  )
}
