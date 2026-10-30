import { notifications } from '@mantine/notifications'

export function notifyError(error: unknown) {
  const message = error instanceof Error ? error.message : 'Something went wrong.'
  notifications.show({ color: 'red', title: 'Could not complete that', message })
}

export function notifySuccess(message: string) {
  notifications.show({ color: 'teal', message })
}
