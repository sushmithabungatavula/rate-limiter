const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function checkRequest({ client_id, algorithm, limit, window_seconds }) {
  const res = await fetch(`${API_URL}/check`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ client_id, algorithm, limit, window_seconds }),
  })
  const data = await res.json()
  return { status: res.status, ...data }
}

export function subscribeToStream(onMessage) {
  const source = new EventSource(`${API_URL}/stream`)
  source.onmessage = (event) => {
    try {
      onMessage(JSON.parse(event.data))
    } catch (err) {
      console.error('Failed to parse SSE payload', err)
    }
  }
  return () => source.close()
}
