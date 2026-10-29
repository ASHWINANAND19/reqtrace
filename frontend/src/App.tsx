import { Container, Text, Title } from '@mantine/core'

export default function App() {
  return (
    <Container size="sm" py="xl">
      <Title order={1}>ReqTrace</Title>
      <Text c="dimmed">Agentic AI assistant for SRS, test cases and traceability.</Text>
    </Container>
  )
}
