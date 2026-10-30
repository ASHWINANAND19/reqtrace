import { Button } from '@mantine/core'
import { IconDownload } from '@tabler/icons-react'
import { useState } from 'react'
import { download } from '../api'
import { notifyError } from '../notify'

/** Downloads an export from the API (FR-08). */
export default function ExportButton({ path, fileName, label }: { path: string; fileName: string; label: string }) {
  const [busy, setBusy] = useState(false)
  return (
    <Button
      variant="default"
      leftSection={<IconDownload size={16} />}
      loading={busy}
      onClick={async () => {
        setBusy(true)
        try {
          await download(path, fileName)
        } catch (err) {
          notifyError(err)
        } finally {
          setBusy(false)
        }
      }}
    >
      {label}
    </Button>
  )
}
