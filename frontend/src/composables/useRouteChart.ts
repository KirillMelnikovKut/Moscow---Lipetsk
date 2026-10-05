import { computed, type Ref } from 'vue'
import type { Analysis, ChartPoint, TelemetryPoint, TerrainPoint } from '../types/domain'
import { sampleSeriesPath } from '../utils/series'

export const plotBounds = { left: 39, right: 310, top: 12, bottom: 116 }

export function useRouteChart(
  terrain: Ref<TerrainPoint[]>,
  telemetry: Ref<TelemetryPoint[]>,
  analysis: Ref<Analysis | null>,
  currentDistance: Ref<number>,
) {
  const routeDistance = computed(() => terrain.value.at(-1)?.distance ?? 0)
  const altitudeMin = computed(() => {
    if (!terrain.value.length) return 0
    let lowest = Infinity
    for (const point of terrain.value) lowest = Math.min(lowest, point.altitude)
    return Math.floor((lowest - 5) / 50) * 50
  })
  const altitudeMax = computed(() => {
    if (!terrain.value.length) return 100
    let highest = -Infinity
    for (const point of terrain.value) highest = Math.max(highest, point.altitude)
    return Math.max(altitudeMin.value + 50, Math.ceil((highest + 5) / 50) * 50)
  })
  const speedMax = computed(() => {
    let observed = 0
    for (const point of telemetry.value) observed = Math.max(observed, point.speed)
    const suggested = analysis.value?.optimal_speed_by_telemetry.reduce((max, value) => Math.max(max, value), 0) ?? 0
    return Math.max(40, Math.ceil(Math.max(observed, suggested) / 20) * 20)
  })
  const fuelMax = computed(() => Math.max(1, Math.ceil((analysis.value?.baseline.fuel_liters ?? 0) / 10) * 10))
  const altitudeTicks = computed(() => [altitudeMax.value, (altitudeMax.value + altitudeMin.value) / 2, altitudeMin.value])
  const speedTicks = computed(() => [speedMax.value, speedMax.value / 2, 0])
  const fuelTicks = computed(() => [fuelMax.value, fuelMax.value / 2, 0])
  const altitudeProfile = computed<ChartPoint[]>(() => terrain.value.map(point => ({ distance: point.distance, value: point.altitude })))
  const speedProfile = computed<ChartPoint[]>(() => telemetry.value.map(point => ({ distance: point.distance, value: point.speed })))
  const recommendedProfile = computed<ChartPoint[]>(() => telemetry.value.map((point, index) => ({
    distance: point.distance, value: analysis.value?.optimal_speed_by_telemetry[index] ?? 0,
  })))
  const fuelProfile = computed<ChartPoint[]>(() => telemetry.value.map((point, index) => ({
    distance: point.distance, value: analysis.value?.fuel_by_telemetry[index] ?? 0,
  })))

  function x(distance: number) {
    const ratio = routeDistance.value ? Math.max(0, Math.min(1, distance / routeDistance.value)) : 0
    return plotBounds.left + ratio * (plotBounds.right - plotBounds.left)
  }
  function y(value: number, min: number, max: number) {
    const ratio = (Math.max(min, Math.min(max, value)) - min) / Math.max(1, max - min)
    return plotBounds.bottom - ratio * (plotBounds.bottom - plotBounds.top)
  }
  function path(points: ChartPoint[], min: number, max: number, area = false) {
    return sampleSeriesPath(points, min, max, x, y, plotBounds.bottom, area)
  }

  const speedPath = computed(() => path(speedProfile.value, 0, speedMax.value))
  const recommendedPath = computed(() => path(recommendedProfile.value, 0, speedMax.value))
  const altitudePath = computed(() => path(altitudeProfile.value, altitudeMin.value, altitudeMax.value))
  const altitudeAreaPath = computed(() => path(altitudeProfile.value, altitudeMin.value, altitudeMax.value, true))
  const fuelPath = computed(() => path(fuelProfile.value, 0, fuelMax.value))
  const fuelAreaPath = computed(() => path(fuelProfile.value, 0, fuelMax.value, true))

  return {
    plotBounds, altitudeMin, altitudeMax, speedMax, fuelMax, altitudeTicks, speedTicks, fuelTicks,
    speedPath, recommendedPath, altitudePath, altitudeAreaPath, fuelPath, fuelAreaPath, x, y, currentDistance,
  }
}
