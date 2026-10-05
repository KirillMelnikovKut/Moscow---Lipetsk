import { computed, onBeforeUnmount, reactive, ref, type Ref } from 'vue'
import type { Analysis, TelemetryPoint, TerrainPoint } from '../types/domain'
import { floorIndex, mix } from '../utils/series'

export function useTripPlayback(
  terrain: Ref<TerrainPoint[]>,
  telemetry: Ref<TelemetryPoint[]>,
  analysis: Ref<Analysis | null>,
) {
  const playTime = ref(0)
  const playing = ref(false)
  const playbackRate = ref(100)
  let frame: number | undefined
  let previousFrame = 0

  const routeDistance = computed(() => terrain.value.at(-1)?.distance ?? 0)
  const tripDuration = computed(() => telemetry.value.at(-1)?.elapsed ?? 0)
  const progress = computed(() => tripDuration.value ? Math.min(1, playTime.value / tripDuration.value) : 0)
  const telemetryIndex = computed(() => floorIndex(telemetry.value, playTime.value, 'elapsed'))
  const currentTelemetry = computed(() => telemetry.value[telemetryIndex.value] ?? null)
  const nextTelemetry = computed(() => telemetry.value[Math.min(telemetryIndex.value + 1, telemetry.value.length - 1)] ?? null)
  const telemetryRatio = computed(() => {
    if (!currentTelemetry.value || !nextTelemetry.value) return 0
    const interval = nextTelemetry.value.elapsed - currentTelemetry.value.elapsed
    return interval > 0 ? Math.max(0, Math.min(1, (playTime.value - currentTelemetry.value.elapsed) / interval)) : 0
  })
  const currentDistance = computed(() => currentTelemetry.value && nextTelemetry.value
    ? mix(currentTelemetry.value.distance, nextTelemetry.value.distance, telemetryRatio.value) : 0)
  const terrainIndex = computed(() => floorIndex(terrain.value, currentDistance.value, 'distance'))
  const currentTerrain = computed(() => terrain.value[terrainIndex.value] ?? null)
  const nextTerrain = computed(() => terrain.value[Math.min(terrainIndex.value + 1, terrain.value.length - 1)] ?? null)
  const terrainRatio = computed(() => {
    if (!currentTerrain.value || !nextTerrain.value) return 0
    const interval = nextTerrain.value.distance - currentTerrain.value.distance
    return interval > 0 ? Math.max(0, Math.min(1, (currentDistance.value - currentTerrain.value.distance) / interval)) : 0
  })
  const coordinate = computed<[number, number]>(() => currentTerrain.value && nextTerrain.value
    ? [mix(currentTerrain.value.lon, nextTerrain.value.lon, terrainRatio.value), mix(currentTerrain.value.lat, nextTerrain.value.lat, terrainRatio.value)]
    : [37.62, 55.75])
  const speed = computed(() => currentTelemetry.value && nextTelemetry.value
    ? mix(currentTelemetry.value.speed, nextTelemetry.value.speed, telemetryRatio.value) : null)
  const engineRpm = computed(() => currentTelemetry.value && nextTelemetry.value
    ? mix(currentTelemetry.value.engine_rpm, nextTelemetry.value.engine_rpm, telemetryRatio.value) : null)
  const rpmAngle = computed(() => -130 + Math.min(1, (engineRpm.value ?? 800) / 7000) * 260)
  const fuel = computed(() => {
    const values = analysis.value?.fuel_by_telemetry
    if (!values?.length || telemetryIndex.value >= values.length) return null
    return mix(values[telemetryIndex.value], values[Math.min(telemetryIndex.value + 1, values.length - 1)], telemetryRatio.value)
  })
  const optimalSpeed = computed(() => analysis.value?.optimal_speed_by_telemetry[telemetryIndex.value] ?? null)
  const predictedSlope = computed(() => analysis.value?.experiment.predicted_slope[terrainIndex.value] ?? null)
  const isFinished = computed(() => tripDuration.value > 0 && playTime.value >= tripDuration.value)

  function animate(now: number) {
    if (!playing.value) return
    if (previousFrame) playTime.value = Math.min(tripDuration.value, playTime.value + (now - previousFrame) / 1000 * playbackRate.value)
    previousFrame = now
    if (isFinished.value) {
      playing.value = false
      previousFrame = 0
      return
    }
    frame = requestAnimationFrame(animate)
  }

  function togglePlayback() {
    if (!telemetry.value.length) return
    if (playing.value) {
      playing.value = false
      if (frame !== undefined) cancelAnimationFrame(frame)
      previousFrame = 0
      return
    }
    if (isFinished.value) playTime.value = 0
    playing.value = true
    previousFrame = 0
    frame = requestAnimationFrame(animate)
  }

  function resetPlayback() {
    playing.value = false
    if (frame !== undefined) cancelAnimationFrame(frame)
    previousFrame = 0
    playTime.value = 0
  }

  function seek(seconds: number) {
    playTime.value = Math.max(0, Math.min(tripDuration.value, seconds))
    previousFrame = 0
  }

  function setPlaybackRate(rate: number) { playbackRate.value = rate }

  onBeforeUnmount(() => { if (frame !== undefined) cancelAnimationFrame(frame) })

  return reactive({
    playTime, playing, playbackRate, routeDistance, tripDuration, progress,
    currentTelemetry, currentDistance, terrainIndex, currentTerrain, coordinate,
    speed, engineRpm, rpmAngle, fuel, optimalSpeed, predictedSlope, isFinished,
    togglePlayback, resetPlayback, seek, setPlaybackRate,
  })
}

export type TripPlaybackState = ReturnType<typeof useTripPlayback>
