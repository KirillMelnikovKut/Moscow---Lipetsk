import type { Analysis, DataEnvelope, DatasetComparison, TelemetryPoint, TerrainPoint } from '../types/domain'

async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url, { cache: 'no-store' })
  const body: unknown = await response.json()
  if (!response.ok) {
    const detail = typeof body === 'object' && body !== null && 'detail' in body
      ? String(body.detail)
      : `HTTP ${response.status}`
    throw new Error(detail)
  }
  return body as T
}

export const routeApi = {
  terrain: () => getJson<DataEnvelope<TerrainPoint>>('/api/route'),
  telemetry: () => getJson<DataEnvelope<TelemetryPoint>>('/api/telemetry'),
  analysis: () => getJson<Analysis>('/api/analysis'),
  datasets: () => getJson<DatasetComparison>('/api/datasets'),
}
