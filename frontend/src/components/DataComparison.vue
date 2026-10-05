<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { Analysis, DatasetComparison } from '../types/domain'
import { formatNumber } from '../utils/format'

const props = defineProps<{ comparison: DatasetComparison | null; analysis: Analysis | null }>()
const page = ref(0)
const pageSize = 100
const labels: Record<string, string> = {
  latitude: 'Широта', longitude: 'Долгота', altitude: 'Высота', slope: 'Уклон', bearing: 'Азимут', speed: 'Скорость',
  vehicle_mass: 'Масса ТС', cargo_mass: 'Масса груза', total_mass: 'Общая масса', engine_rpm: 'Обороты',
  throttle: 'Газ', brake: 'Тормоз', acceleration: 'Ускорение',
}
const differences = computed(() => props.comparison?.differences ?? [])
const pageCount = computed(() => Math.max(1, Math.ceil(differences.value.length / pageSize)))
const visibleRows = computed(() => differences.value.slice(page.value * pageSize, (page.value + 1) * pageSize))
const fields = computed(() => Object.entries(props.comparison?.field_counts ?? {}).filter(([, count]) => count > 0))
const summary = computed(() => props.comparison ? {
  count: props.comparison.masked_count,
  fields: fields.value.length,
  rows: props.comparison.row_count,
} : null)
watch(() => props.comparison, () => { page.value = 0 })
</script>

<template>
  <section class="side-section data-view">
    <div class="section-kicker">ТРИ ВЕРСИИ ОДНОГО НАБОРА</div>
    <h2>Реальные и восстановленные значения</h2>
    <p class="tab-intro">Полные данные, версия с пропусками и результат восстановления.</p>
    <div class="dataset-file-list">
      <div><b>1</b><span><strong>full_data.csv</strong><small>Исходный набор</small></span></div>
      <div><b>2</b><span><strong>missing_data.csv</strong><small>Случайные пустые значения</small></span></div>
      <div><b>3</b><span><strong>restored_data.csv</strong><small>Заполненные пропуски · источник интерфейса</small></span></div>
    </div>
    <div v-if="summary" class="data-summary">
      <div><span>Восстановлено значений</span><strong>{{ formatNumber(summary.count) }}</strong></div>
      <div><span>Полей с пропусками</span><strong>{{ formatNumber(summary.fields) }}</strong></div>
      <div><span>Точек маршрута</span><strong>{{ formatNumber(summary.rows) }}</strong></div>
    </div>
    <div class="compare-metrics">
      <div><span>KNN · MAE</span><strong>{{ formatNumber(analysis?.experiment.metrics.ml_mae_m, 2) }} м</strong></div>
      <div><span>Линейная · MAE</span><strong>{{ formatNumber(analysis?.experiment.metrics.linear_mae_m, 2) }} м</strong></div>
      <div><span>KNN · RMSE</span><strong>{{ formatNumber(analysis?.experiment.metrics.ml_rmse_m, 2) }} м</strong></div>
      <div><span>Линейная · RMSE</span><strong>{{ formatNumber(analysis?.experiment.metrics.linear_rmse_m, 2) }} м</strong></div>
    </div>
    <div class="table-tools">
      <span>{{ formatNumber(differences.length) }} пропусков · страница {{ page + 1 }} / {{ pageCount }}</span>
      <div><button type="button" :disabled="page === 0" @click="page--">←</button><button type="button" :disabled="page + 1 >= pageCount" @click="page++">→</button></div>
    </div>
    <div class="field-counts">
      <span v-for="[field, count] in fields" :key="field">{{ labels[field] ?? field }} · {{ formatNumber(count) }} · MAE {{ formatNumber(comparison?.field_metrics[field]?.mae, 3) }}</span>
    </div>
    <div class="comparison-table-wrap">
      <table class="comparison-table">
        <thead><tr><th>Поле</th><th>Точка</th><th>Реальные</th><th>Пустые</th><th>Восстановл.</th><th>Δ</th></tr></thead>
        <tbody>
          <tr v-for="point in visibleRows" :key="`${point.point_id}-${point.field}`" class="reconstructed">
            <td>{{ labels[point.field] ?? point.field }}</td><td>{{ point.point_id }}</td>
            <td>{{ formatNumber(Number(point.real), 3) }}</td><td>—</td><td>{{ formatNumber(Number(point.restored), 3) }}</td>
            <td><span class="error-pill">{{ point.delta == null ? '—' : formatNumber(point.delta, 3) }}</span></td>
          </tr>
          <tr v-if="!comparison"><td colspan="6" class="empty-table">Загрузка сравнения…</td></tr>
          <tr v-else-if="!differences.length"><td colspan="6" class="empty-table">Пропусков не найдено.</td></tr>
        </tbody>
      </table>
    </div>
    <p class="chart-note">MAE в списке рассчитана отдельно для каждого поля. Δ — восстановленное значение минус исходное.</p>
  </section>
</template>
