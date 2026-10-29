import { Alert, Button, Card, Group, Loader, Stack, Text, Textarea, Title } from '@mantine/core'
import { IconCode, IconPhotoDown, IconRefresh, IconSparkles } from '@tabler/icons-react'
import { useEffect, useRef, useState } from 'react'
import { get, post, put } from '../api'
import { useAuth } from '../auth'
import { notifyError, notifySuccess } from '../notify'
import { svgToPng } from '../png'
import type { ProjectTabProps } from '../pages/ProjectPage'
import type { Diagram } from '../types'
import MermaidView from './MermaidView'

function DiagramCard({ projectId, diagram, canEdit }: { projectId: number; diagram: Diagram; canEdit: boolean }) {
  const [current, setCurrent] = useState(diagram)
  const [draft, setDraft] = useState<string | null>(null)
  const viewRef = useRef<HTMLDivElement>(null)

  async function exportPng() {
    const svg = viewRef.current?.querySelector<SVGSVGElement>('.mermaid-diagram svg')
    if (!svg) return notifyError(new Error('The diagram has not rendered yet.'))
    try {
      await svgToPng(svg, `${diagram.kind}-diagram.png`)
      post(`/projects/${projectId}/export/diagram-png?kind=${diagram.kind}`).catch(() => undefined)
    } catch (err) {
      notifyError(err)
    }
  }

  async function rerender() {
    if (draft === null) return
    try {
      setCurrent(await put<Diagram>(`/projects/${projectId}/diagrams/${diagram.kind}`, { source: draft }))
      setDraft(null)
      notifySuccess(`${diagram.title} updated`)
    } catch (err) {
      notifyError(err)
    }
  }

  return (
    <Card withBorder>
      <Group justify="space-between" mb="sm">
        <div>
          <Title order={4}>{current.title}</Title>
          <Text size="xs" c="dimmed">
            From SRS v{current.srs_version_no}
          </Text>
        </div>
        <Group>
          {draft === null && (
            <Button variant="default" size="xs" leftSection={<IconPhotoDown size={14} />} onClick={exportPng}>
              Export PNG
            </Button>
          )}
          {canEdit && (
            <Group>
              {draft === null ? (
                <Button
                  variant="default"
                  size="xs"
                  leftSection={<IconCode size={14} />}
                  onClick={() => setDraft(current.source)}
                >
                  Edit source
                </Button>
              ) : (
                <>
                  <Button variant="default" size="xs" onClick={() => setDraft(null)}>
                    Cancel
                  </Button>
                  <Button size="xs" leftSection={<IconRefresh size={14} />} onClick={rerender}>
                    Save and re-render
                  </Button>
                </>
              )}
            </Group>
          )}
        </Group>
      </Group>
      {draft !== null && (
        <Textarea
          ff="monospace"
          autosize
          minRows={6}
          maxRows={20}
          mb="sm"
          value={draft}
          onChange={(e) => setDraft(e.currentTarget.value)}
          aria-label={`${current.title} source`}
        />
      )}
      <div ref={viewRef}>
        <MermaidView source={draft ?? current.source} />
      </div>
    </Card>
  )
}

/** UML diagrams generated from the approved SRS (FR-10). */
export default function DiagramsTab({ project }: ProjectTabProps) {
  const { can } = useAuth()
  const canEdit = can('Developer', 'Analyst', 'Administrator')
  const [diagrams, setDiagrams] = useState<Diagram[] | null>(null)
  const [generation, setGeneration] = useState(0)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    get<Diagram[]>(`/projects/${project.id}/diagrams`).then(setDiagrams).catch(notifyError)
  }, [project.id])

  async function generate() {
    setBusy(true)
    setError('')
    try {
      setDiagrams(await post<Diagram[]>(`/projects/${project.id}/diagrams/generate`))
      setGeneration((g) => g + 1)
      notifySuccess('Diagrams generated')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Generation failed.')
    } finally {
      setBusy(false)
    }
  }

  if (!diagrams) return <Loader />

  return (
    <Stack>
      <Card withBorder>
        <Group justify="space-between">
          <Text size="sm" c="dimmed">
            {diagrams.length
              ? 'Use-case, class and sequence diagrams. Edit the source to correct them.'
              : 'No diagrams yet.'}
          </Text>
          {canEdit && (
            <Button leftSection={<IconSparkles size={16} />} loading={busy} onClick={generate}>
              Generate diagrams
            </Button>
          )}
        </Group>
        {error && (
          <Alert color="red" mt="sm">
            {error}
          </Alert>
        )}
      </Card>
      {diagrams.map((d) => (
        <DiagramCard key={`${d.kind}-${generation}`} projectId={project.id} diagram={d} canEdit={canEdit} />
      ))}
    </Stack>
  )
}
