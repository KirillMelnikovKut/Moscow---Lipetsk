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

export type RouteSegment = {
  id: number
  name: string
  title: string
  from_km: number
  to_km: number
  length_km: number
  is_toll: boolean
  speed_kmh: number
  duration_min: number
  fuel_liters: number
  fuel_per_100km: number
  toll_rub: number
  wear_rub: number
  fuel_cost_rub: number
}

export type RouteSegmentDef = {
  id: number
  name: string
  from_km: number
  to_km: number
  length_km: number
  bottleneck: boolean
  toll_name: string
  free_name: string
  toll_day: number
  toll_night: number
}

export type RouteOptimizationVariant = {
  id: string
  name: string
  description: string
  departure_time: string
  is_night?: boolean
  distance_km: number
  duration_hours: number
  avg_speed_kmh: number
  fuel_liters: number
  fuel_per_100km: number
  fuel_cost_rub: number
  toll_cost_rub: number
  wear_cost_rub: number
  time_cost_rub: number
  total_cost_rub: number
  segments: RouteSegment[]
}

export type RouteOptimizationResult = {
  params: {
    fuel_price: number
    value_of_time: number
    vehicle_type: string
    vehicle_mass: number
  }
  segments_def: RouteSegmentDef[]
  variants: RouteOptimizationVariant[]
  best_variant_id: string
  savings_vs_toll: number
  savings_vs_free: number
  methodology_summary: {
    title: string
    points: string[]
  }
}

export type ActiveTab = 'dashboard' | 'data' | 'routes'
