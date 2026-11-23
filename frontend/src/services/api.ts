import type {
  Analysis,
  DataEnvelope,
  DatasetComparison,
  RouteOptimizationResult,
  TelemetryPoint,
  TerrainPoint,
} from '../types/domain'

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
  optimization: (params?: { fuelPrice?: number; valueOfTime?: number; vehicleType?: string }) => {
    const q = new URLSearchParams()
    if (params?.fuelPrice !== undefined) q.set('fuel_price', String(params.fuelPrice))
    if (params?.valueOfTime !== undefined) q.set('value_of_time', String(params.valueOfTime))
    if (params?.vehicleType !== undefined) q.set('vehicle_type', params.vehicleType)
    const qs = q.toString()
    return getJson<RouteOptimizationResult>(`/api/optimization${qs ? `?${qs}` : ''}`)
  },
}
