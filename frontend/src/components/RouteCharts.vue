<script setup lang="ts">
import { toRef } from 'vue'
import { useRouteChart } from '../composables/useRouteChart'
import type { Analysis, TelemetryPoint, TerrainPoint } from '../types/domain'
import { formatNumber } from '../utils/format'

const props = defineProps<{
  terrain: TerrainPoint[]; telemetry: TelemetryPoint[]; analysis: Analysis | null
  currentDistance: number; currentSpeed: number | null; currentFuel: number | null
  currentAltitude: number | null; currentSlope: number | null
}>()
const { plotBounds, altitudeMin, altitudeMax, speedMax, fuelMax, altitudeTicks, speedTicks, fuelTicks,
  speedPath, recommendedPath, altitudePath, altitudeAreaPath, fuelPath, fuelAreaPath, x, y } = useRouteChart(
  toRef(props, 'terrain'), toRef(props, 'telemetry'), toRef(props, 'analysis'), toRef(props, 'currentDistance'),
)
</script>

<template>
  <section class="side-section terrain-section">
    <div class="section-heading"><span class="section-kicker">КАК МЕНЯЕТСЯ ПОЕЗДКА</span><span class="file-tag">по километрам</span></div>
    <article class="route-chart-card">
      <div class="chart-card-heading"><div><h3>Скорость</h3><span>Фактическая и рекомендуемая</span></div><strong>{{ formatNumber(currentSpeed, 1) }} <small>км/ч сейчас</small></strong></div>
      <div class="chart-legend"><span><i class="legend-speed"></i> Поездка</span><span><i class="legend-recommended"></i> Рекомендация</span></div>
      <svg class="route-chart" viewBox="0 0 320 151" role="img" aria-label="Скорость автомобиля по маршруту в километрах в час">
        <g v-for="tick in speedTicks" :key="`speed-${tick}`"><line :x1="plotBounds.left" :x2="plotBounds.right" :y1="y(tick, 0, speedMax)" :y2="y(tick, 0, speedMax)" class="plot-grid"/><text :x="plotBounds.left - 7" :y="y(tick, 0, speedMax) + 3" class="plot-label" text-anchor="end">{{ formatNumber(tick) }}</text></g>
        <path :d="speedPath" class="series-speed"/><path v-if="analysis" :d="recommendedPath" class="series-recommended"/>
        <line :x1="x(currentDistance)" :x2="x(currentDistance)" :y1="plotBounds.top" :y2="plotBounds.bottom" class="plot-cursor"/><circle :cx="x(currentDistance)" :cy="y(currentSpeed ?? 0, 0, speedMax)" r="4" class="plot-current-speed"/>
        <text :x="plotBounds.left" y="141" class="plot-label" text-anchor="middle">0 км</text><text :x="(plotBounds.left + plotBounds.right) / 2" y="141" class="plot-label" text-anchor="middle">{{ formatNumber((terrain.at(-1)?.distance ?? 0) / 2000, 0) }} км</text><text :x="plotBounds.right" y="141" class="plot-label" text-anchor="end">{{ formatNumber((terrain.at(-1)?.distance ?? 0) / 1000, 0) }} км</text>
      </svg>
      <div class="chart-axis-caption"><span>Скорость, км/ч</span><span>Расстояние по маршруту</span></div>
    </article>
    <article class="route-chart-card elevation-card">
      <div class="chart-card-heading"><div><h3>Высота маршрута</h3><span>Профиль дороги от Москвы до Липецка</span></div><strong>{{ formatNumber(currentAltitude, 1) }} <small>м сейчас</small></strong></div>
      <svg class="route-chart" viewBox="0 0 320 151" role="img" aria-label="Высота местности по маршруту в метрах">
        <g v-for="tick in altitudeTicks" :key="`altitude-${tick}`"><line :x1="plotBounds.left" :x2="plotBounds.right" :y1="y(tick, altitudeMin, altitudeMax)" :y2="y(tick, altitudeMin, altitudeMax)" class="plot-grid"/><text :x="plotBounds.left - 7" :y="y(tick, altitudeMin, altitudeMax) + 3" class="plot-label" text-anchor="end">{{ formatNumber(tick) }}</text></g>
        <path :d="altitudeAreaPath" class="elevation-fill"/><path :d="altitudePath" class="series-elevation"/>
        <line :x1="x(currentDistance)" :x2="x(currentDistance)" :y1="plotBounds.top" :y2="plotBounds.bottom" class="plot-cursor"/><circle :cx="x(currentDistance)" :cy="y(currentAltitude ?? altitudeMin, altitudeMin, altitudeMax)" r="4" class="plot-current-elevation"/>
        <text :x="plotBounds.left" y="141" class="plot-label" text-anchor="middle">0 км</text><text :x="(plotBounds.left + plotBounds.right) / 2" y="141" class="plot-label" text-anchor="middle">{{ formatNumber((terrain.at(-1)?.distance ?? 0) / 2000, 0) }} км</text><text :x="plotBounds.right" y="141" class="plot-label" text-anchor="end">{{ formatNumber((terrain.at(-1)?.distance ?? 0) / 1000, 0) }} км</text>
      </svg>
      <div class="chart-axis-caption"><span>Высота над уровнем моря, м</span><span>Текущий уклон: {{ formatNumber(currentSlope, 2) }} %</span></div>
    </article>
    <article class="route-chart-card fuel-card">
      <div class="chart-card-heading"><div><h3>Расход топлива</h3><span>Накоплено с начала поездки</span></div><strong>{{ formatNumber(currentFuel, 2) }} <small>л сейчас</small></strong></div>
      <svg class="route-chart" viewBox="0 0 320 151" role="img" aria-label="Накопленный расход топлива по маршруту в литрах">
        <g v-for="tick in fuelTicks" :key="`fuel-${tick}`"><line :x1="plotBounds.left" :x2="plotBounds.right" :y1="y(tick, 0, fuelMax)" :y2="y(tick, 0, fuelMax)" class="plot-grid"/><text :x="plotBounds.left - 7" :y="y(tick, 0, fuelMax) + 3" class="plot-label" text-anchor="end">{{ formatNumber(tick) }}</text></g>
        <path :d="fuelAreaPath" class="fuel-fill"/><path :d="fuelPath" class="series-fuel"/>
        <line :x1="x(currentDistance)" :x2="x(currentDistance)" :y1="plotBounds.top" :y2="plotBounds.bottom" class="plot-cursor"/><circle :cx="x(currentDistance)" :cy="y(currentFuel ?? 0, 0, fuelMax)" r="4" class="plot-current-fuel"/>
        <text :x="plotBounds.left" y="141" class="plot-label" text-anchor="middle">0 км</text><text :x="(plotBounds.left + plotBounds.right) / 2" y="141" class="plot-label" text-anchor="middle">{{ formatNumber((terrain.at(-1)?.distance ?? 0) / 2000, 0) }} км</text><text :x="plotBounds.right" y="141" class="plot-label" text-anchor="end">{{ formatNumber((terrain.at(-1)?.distance ?? 0) / 1000, 0) }} км</text>
      </svg>
      <div class="chart-axis-caption"><span>Израсходовано, л</span><span>Оценка модели</span></div>
    </article>
    <p class="chart-note">Вертикальная линия показывает текущее положение автомобиля. Шкала высоты подстраивается под профиль этого маршрута.</p>
  </section>
</template>
