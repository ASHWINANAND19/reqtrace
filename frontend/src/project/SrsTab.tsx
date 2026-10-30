import { Alert, Badge, Button, Card, Group, Loader, Select, Stack, Text } from '@mantine/core'
import { IconCircleCheck, IconGitCompare, IconPencil, IconSparkles, IconZoomCheck } from '@tabler/icons-react'
import { useCallback, useEffect, useState } from 'react'
import { get, post } from '../api'
import { useAuth } from '../auth'
import { formatDate } from '../format'
import { notifyError, notifySuccess } from '../notify'
import type { ProjectTabProps } from '../pages/ProjectPage'
import type { QualityReport, SrsSummary, SrsVersion } from '../types'
import CompareModal from './CompareModal'
import QualityPanel from './QualityPanel'
import SrsDocument from './SrsDocument'
import SrsEditor from './SrsEditor'

export default function SrsTab({ project }: ProjectTabProps) {
  const { can } = useAuth()
  const [versions, setVersions] = useState<SrsSummary[] | null>(null)
  const [selected, setSelected] = useState<string | null>(null)
  const [loaded, setLoaded] = useState<SrsVersion | null>(null)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')
  const [editing, setEditing] = useState(false)
  const [comparing, setComparing] = useState(false)
  const [quality, setQuality] = useState<QualityReport | null>(null)
  const [checking, setChecking] = useState(false)
  const base = `/projects/${project.id}/srs`
  const canEdit = can('Analyst', 'Administrator')

  const loadVersions = useCallback(
    (select?: number) =>
      get<SrsSummary[]>(`${base}/versions`)
        .then((list) => {
          setVersions(list)
          setSelected((current) => String(select ?? (current ? Number(current) : list[0]?.id ?? '')) || null)
        })
        .catch(notifyError),
    [base],
  )

  useEffect(() => {
    loadVersions()
  }, [loadVersions])

  useEffect(() => {
    if (selected) get<SrsVersion>(`${base}/versions/${selected}`).then(setLoaded).catch(notifyError)
  }, [base, selected])

  const version = loaded && String(loaded.id) === selected ? loaded : null

  async function generate() {
    setGenerating(true)
    setError('')
    try {
      const created = await post<SrsVersion>(`${base}/generate`)
      notifySuccess(`SRS version ${created.version_no} generated`)
      await loadVersions(created.id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Generation failed.')
    } finally {
      setGenerating(false)
    }
  }

  async function approve() {
    if (!version) return
    try {
      const approved = await post<SrsVersion>(`${base}/versions/${version.id}/approve`)
      setLoaded(approved)
      notifySuccess(`Version ${approved.version_no} approved`)
      loadVersions(approved.id)
    } catch (err) {
      notifyError(err)
    }
  }

  async function checkQuality() {
    if (!version) return
    setChecking(true)
    try {
      setQuality(await post<QualityReport>(`${base}/versions/${version.id}/check`))
    } catch (err) {
      notifyError(err)
    } finally {
      setChecking(false)
    }
  }

  if (versions === null) return <Loader />

  if (editing && version) {
    return (
      <SrsEditor
        projectId={project.id}
        version={version}
        onCancel={() => setEditing(false)}
        onSaved={(saved) => {
          setEditing(false)
          loadVersions(saved.id)
        }}
      />
    )
  }

  return (
    <Stack>
      <Card withBorder>
        <Group justify="space-between">
          <Group>
            <Select
              label="Version"
              placeholder="No SRS yet"
              data={versions.map((v) => ({
                value: String(v.id),
                label: `v${v.version_no} · ${v.status} · ${v.source}`,
              }))}
              value={selected}
              onChange={(v) => {
                setSelected(v)
                setQuality(null)
              }}
              allowDeselect={false}
              w={260}
            />
            {version && (
              <Stack gap={2}>
                <Group gap="xs">
                  <Badge color={version.status === 'approved' ? 'teal' : 'blue'}>{version.status}</Badge>
                  <Text size="xs" c="dimmed">
                    by {version.author_name} · {formatDate(version.created_at)}
                  </Text>
                </Group>
                {version.approved_by_name && (
                  <Text size="xs" c="dimmed">
                    Approved by {version.approved_by_name} · {formatDate(version.approved_at)}
                  </Text>
                )}
              </Stack>
            )}
          </Group>
          <Group>
            {version && (
              <Button variant="default" leftSection={<IconZoomCheck size={16} />} loading={checking} onClick={checkQuality}>
                Check quality
              </Button>
            )}
            {versions.length > 1 && (
              <Button variant="default" leftSection={<IconGitCompare size={16} />} onClick={() => setComparing(true)}>
                Compare
              </Button>
            )}
            {canEdit && version && (
              <Button variant="default" leftSection={<IconPencil size={16} />} onClick={() => setEditing(true)}>
                Edit
              </Button>
            )}
            {canEdit && version?.status === 'draft' && (
              <Button color="teal" variant="light" leftSection={<IconCircleCheck size={16} />} onClick={approve}>
                Approve
              </Button>
            )}
            {canEdit && (
              <Button leftSection={<IconSparkles size={16} />} loading={generating} onClick={generate}>
                Generate SRS
              </Button>
            )}
          </Group>
        </Group>
        {generating && (
          <Group mt="sm" gap="xs">
            <Loader size="xs" />
            <Text size="sm" c="dimmed">
              The SRS agent is drafting the IEEE 830 document. This can take up to a minute…
            </Text>
          </Group>
        )}
        {error && (
          <Alert color="red" mt="sm">
            {error}
          </Alert>
        )}
      </Card>

      {versions.length === 0 && !generating && (
        <Text c="dimmed">Add requirements on the Input tab, then generate the first SRS draft.</Text>
      )}
      {quality && <QualityPanel report={quality} onClose={() => setQuality(null)} />}
      {version && (
        <Card withBorder>
          <SrsDocument version={version} />
        </Card>
      )}
      {comparing && (
        <CompareModal projectId={project.id} versions={versions} opened={comparing} onClose={() => setComparing(false)} />
      )}
    </Stack>
  )
}
