export type HealthResponse = {
  status: string
  service: string
}

const defaultBaseUrl = import.meta.env.DEV ? 'http://localhost:8000/api/v1' : '/api/v1'
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? defaultBaseUrl

export async function fetchHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch(`${apiBaseUrl}/health`, {
    signal,
  })

  if (!response.ok) {
    throw new Error(`Health request failed with status ${response.status}`)
  }

  return (await response.json()) as HealthResponse
}
