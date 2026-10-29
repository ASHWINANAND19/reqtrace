import { Alert, Box, Loader } from '@mantine/core'
import { useEffect, useId, useState } from 'react'

// Mermaid renders through shared global state, so renders must run one at a time.
let queue: Promise<unknown> = Promise.resolve()

function renderMermaid(id: string, source: string): Promise<string> {
  const job = queue.then(async () => {
    const { default: mermaid } = await import('mermaid') // loaded on demand to keep the main bundle small
    mermaid.initialize({ startOnLoad: false, securityLevel: 'strict', theme: 'default' })
    try {
      return (await mermaid.render(id, source)).svg
    } finally {
      document.getElementById('d' + id)?.remove() // mermaid leaves a temporary node behind on errors
    }
  })
  queue = job.catch(() => undefined)
  return job
}

/** Renders Mermaid source to SVG on a white background (the same look as the PNG export). */
export default function MermaidView({ source }: { source: string }) {
  const id = 'mmd' + useId().replace(/[^a-zA-Z0-9]/g, '')
  const [result, setResult] = useState<{ source: string; svg?: string; error?: string } | null>(null)

  useEffect(() => {
    let cancelled = false
    renderMermaid(id, source)
      .then((svg) => !cancelled && setResult({ source, svg }))
      .catch((err: unknown) => !cancelled && setResult({ source, error: err instanceof Error ? err.message : String(err) }))
    return () => {
      cancelled = true
    }
  }, [id, source])

  if (!result || result.source !== source) return <Loader size="sm" />
  if (result.error) {
    return (
      <Alert color="red" title="This diagram source has a syntax error">
        {result.error.split('\n').slice(0, 3).join(' ')}
      </Alert>
    )
  }
  // Mermaid output is sanitised (securityLevel: strict)
  return (
    <Box
      className="mermaid-diagram"
      bg="white"
      p="md"
      style={{ overflowX: 'auto', borderRadius: 8 }}
      dangerouslySetInnerHTML={{ __html: result.svg ?? '' }}
    />
  )
}
