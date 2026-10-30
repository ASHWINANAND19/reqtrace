import {
  ActionIcon,
  Badge,
  Button,
  Card,
  FileInput,
  Group,
  ScrollArea,
  Stack,
  Text,
  Textarea,
  Title,
} from '@mantine/core'
import { IconFileUpload, IconTrash } from '@tabler/icons-react'
import { useCallback, useEffect, useState } from 'react'
import { del, get, post } from '../api'
import { useAuth } from '../auth'
import { notifyError, notifySuccess } from '../notify'
import type { ProjectTabProps } from '../pages/ProjectPage'
import type { RequirementInput } from '../types'

export default function InputTab({ project }: ProjectTabProps) {
  const { can } = useAuth()
  const canEdit = can('Analyst', 'Administrator')
  const [inputs, setInputs] = useState<RequirementInput[]>([])
  const [text, setText] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)

  const load = useCallback(() => {
    get<RequirementInput[]>(`/projects/${project.id}/inputs`).then(setInputs).catch(notifyError)
  }, [project.id])
  useEffect(load, [load])

  async function submit(action: () => Promise<unknown>, done: () => void) {
    setBusy(true)
    try {
      await action()
      done()
      notifySuccess('Requirements saved')
      load()
    } catch (err) {
      notifyError(err)
    } finally {
      setBusy(false)
    }
  }

  function uploadFile() {
    if (!file) return
    const form = new FormData()
    form.append('file', file)
    submit(() => post(`/projects/${project.id}/inputs/file`, form), () => setFile(null))
  }

  return (
    <Stack>
      {canEdit && (
        <Card withBorder>
          <Title order={4} mb="sm">
            Add raw requirements
          </Title>
          <Textarea
            placeholder="Paste or type requirements, one per line or as free text…"
            autosize
            minRows={5}
            maxRows={14}
            value={text}
            onChange={(e) => setText(e.currentTarget.value)}
          />
          <Group justify="flex-end" mt="sm">
            <Button
              disabled={!text.trim()}
              loading={busy}
              onClick={() => submit(() => post(`/projects/${project.id}/inputs/text`, { content: text }), () => setText(''))}
            >
              Save text
            </Button>
          </Group>
          <Group mt="md" align="flex-end">
            <FileInput
              label="Or upload a document"
              description="TXT, DOCX or PDF, up to 10 MB"
              accept=".txt,.docx,.pdf"
              clearable
              value={file}
              onChange={setFile}
              leftSection={<IconFileUpload size={16} />}
              style={{ flex: 1 }}
            />
            <Button disabled={!file} loading={busy} onClick={uploadFile}>
              Upload
            </Button>
          </Group>
        </Card>
      )}

      <Title order={4}>Saved input ({inputs.length})</Title>
      {inputs.length === 0 && <Text c="dimmed">No requirements yet.</Text>}
      {inputs.map((item) => (
        <Card key={item.id} withBorder>
          <Group justify="space-between" mb="xs">
            <Group gap="xs">
              <Badge variant="light">{item.kind === 'file' ? 'File' : 'Text'}</Badge>
              {item.filename && <Text fw={500}>{item.filename}</Text>}
              <Text size="xs" c="dimmed">
                {item.author_name} · {new Date(item.created_at + 'Z').toLocaleString()}
              </Text>
            </Group>
            {canEdit && (
              <ActionIcon
                variant="subtle"
                color="red"
                aria-label="Delete input"
                onClick={() => submit(() => del(`/projects/${project.id}/inputs/${item.id}`), () => undefined)}
              >
                <IconTrash size={16} />
              </ActionIcon>
            )}
          </Group>
          <ScrollArea.Autosize mah={180}>
            <Text size="sm" style={{ whiteSpace: 'pre-wrap' }}>
              {item.content}
            </Text>
          </ScrollArea.Autosize>
        </Card>
      ))}
    </Stack>
  )
}
