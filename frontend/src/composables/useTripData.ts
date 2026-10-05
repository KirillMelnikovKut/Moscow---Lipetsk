import { onMounted, ref } from 'vue'
import { routeApi } from '../services/api'
import type { Analysis, DatasetComparison, TelemetryPoint, TerrainPoint } from '../types/domain'

export function useTripData() {
  const terrain = ref<TerrainPoint[]>([])
  const telemetry = ref<TelemetryPoint[]>([])
  const analysis = ref<Analysis | null>(null)
  const comparison = ref<DatasetComparison | null>(null)
  const terrainVersion = ref<string | null>(null)
  const telemetryVersion = ref<string | null>(null)
  const terrainMessage = ref('Загрузка маршрута…')
  const telemetryMessage = ref('Загрузка телеметрии…')
  const analysisMessage = ref('Подготовка расчётов…')
  async function load() {
    const [routeResult, telemetryResult, comparisonResult] = await Promise.allSettled([
      routeApi.terrain(), routeApi.telemetry(), routeApi.datasets(),
    ])

    if (routeResult.status === 'fulfilled') {
      terrain.value = routeResult.value.points
      terrainVersion.value = routeResult.value.version
      terrainMessage.value = `Маршрут · ${routeResult.value.points.length.toLocaleString('ru-RU')} точек`
    } else terrainMessage.value = `Не удалось загрузить маршрут: ${String(routeResult.reason)}`

    if (telemetryResult.status === 'fulfilled') {
      telemetry.value = telemetryResult.value.points
      telemetryVersion.value = telemetryResult.value.version
      telemetryMessage.value = `Телеметрия · ${telemetryResult.value.points.length.toLocaleString('ru-RU')} строк`
    } else telemetryMessage.value = `Не удалось загрузить телеметрию: ${String(telemetryResult.reason)}`

    if (comparisonResult.status === 'fulfilled') comparison.value = comparisonResult.value
    else analysisMessage.value = `Не удалось загрузить сравнение файлов: ${String(comparisonResult.reason)}`

    if (terrain.value.length && telemetry.value.length) {
      try {
        const result = await routeApi.analysis()
        if (result.terrain_version === terrainVersion.value && result.telemetry_version === telemetryVersion.value) {
          analysis.value = result
          analysisMessage.value = 'Расчёты модели готовы'
        } else analysisMessage.value = 'Версия модели не совпала с загруженными данными'
      } catch (error) {
        analysisMessage.value = `Не удалось рассчитать модель: ${String(error)}`
      }
    }
  }

  onMounted(() => { void load() })

  return { terrain, telemetry, analysis, comparison, terrainMessage, telemetryMessage, analysisMessage }
}
