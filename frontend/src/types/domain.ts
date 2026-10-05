export type TerrainPoint = {
  id: number
  lat: number
  lon: number
  altitude: number
  slope: number
  distance: number
  bearing: number | null
}

export type TelemetryPoint = {
  id: number
  distance: number
  elapsed: number
  speed: number
  engine_rpm: number
  engine_rpm_estimated?: boolean
  vehicle_mass: number
  cargo_mass: number
  total_mass: number
}

export type DatasetDifference = {
  point_id: string
  distance: string
  field: string
  real: string
  missing: string
  restored: string
  delta: number | null
}

export type DatasetComparison = {
  full_version: string
  missing_version: string
  restored_version: string
  row_count: number
  masked_count: number
  field_counts: Record<string, number>
  field_metrics: Record<string, { mae: number; rmse: number; count: number }>
  differences: DatasetDifference[]
}

export type Analysis = {
  terrain_version: string
  telemetry_version: string
  experiment: {
    predicted_slope: number[]
    metrics: {
      removed_count: number
      total_count: number
      ml_mae_m: number
      ml_rmse_m: number
      linear_mae_m: number
      linear_rmse_m: number
      model: string
    }
  }
  fuel_by_telemetry: number[]
  optimal_speed_by_telemetry: number[]
  baseline: { duration_seconds: number; fuel_liters: number }
  optimal: { duration_seconds: number; fuel_liters: number; cap_kmh: number }
}

export type DataEnvelope<T> = { version: string; points: T[] }
export type ChartPoint = { distance: number; value: number }
export type ActiveTab = 'dashboard' | 'data'
