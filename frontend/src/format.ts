/** API timestamps are naive UTC; show them in the viewer's local time. */
export function formatDate(value: string | null | undefined) {
  return value ? new Date(value + 'Z').toLocaleString() : ''
}

export const PRIORITY_COLOR: Record<string, string> = { Must: 'red', Should: 'orange', Could: 'yellow' }
