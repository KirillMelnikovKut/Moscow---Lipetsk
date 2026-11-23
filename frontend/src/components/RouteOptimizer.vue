<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { routeApi } from '../services/api'
import type { RouteOptimizationResult, RouteSegment, TerrainPoint } from '../types/domain'
import type { TripPlaybackState } from '../composables/useTripPlayback'

const props = defineProps<{
  playback?: TripPlaybackState
  terrain?: TerrainPoint[]
}>()

const emit = defineEmits<{
  'update:segments': [segments: RouteSegment[]]
}>()
const fuelPrice = ref(68)
const valueOfTime = ref(600)
const vehicleType = ref<'car' | 'van'>('car')
const activePreset = ref<'toll' | 'free' | 'hybrid' | 'custom'>('hybrid')
const isNight = ref(true)
const customTollFlags = ref<Record<number, boolean>>({
  1: true,
  2: false,
  3: true,
  4: false,
  5: true,
  6: false,
})

const loading = ref(false)
const error = ref<string | null>(null)
const apiData = ref<RouteOptimizationResult | null>(null)

async function loadOptimization() {
  loading.value = true
  error.value = null
  try {
    apiData.value = await routeApi.optimization({
      fuelPrice: fuelPrice.value,
      valueOfTime: valueOfTime.value,
      vehicleType: vehicleType.value,
    })
  } catch (err) {
    error.value = String(err)
  } finally {
    loading.value = false
  }
}

watch([fuelPrice, valueOfTime, vehicleType], () => {
  void loadOptimization()
})

onMounted(() => {
  void loadOptimization()
})

function selectPreset(preset: 'toll' | 'free' | 'hybrid' | 'custom') {
  activePreset.value = preset
  if (preset === 'toll') {
    isNight.value = false
    customTollFlags.value = { 1: true, 2: true, 3: true, 4: true, 5: true, 6: true }
  } else if (preset === 'free') {
    isNight.value = false
    customTollFlags.value = { 1: false, 2: false, 3: false, 4: false, 5: false, 6: false }
  } else if (preset === 'hybrid') {
    isNight.value = true
    customTollFlags.value = { 1: true, 2: false, 3: true, 4: false, 5: true, 6: false }
  }
}

function toggleSegment(id: number) {
  customTollFlags.value[id] = !customTollFlags.value[id]
  activePreset.value = 'custom'
}
const currentSegments = computed<RouteSegment[]>(() => {
  if (!apiData.value) return []
  if (activePreset.value !== 'custom') {
    const v = apiData.value.variants.find((item) => item.id === activePreset.value)
    if (v) return v.segments
  }
  const mass = vehicleType.value === 'van' ? 2800 : 1650
  const cda = vehicleType.value === 'van' ? 2.2 : 0.77
  const crr = vehicleType.value === 'van' ? 0.01 : 0.009
  const eta = 0.28
  const qFuel = 35_000_000
  const idleLph = vehicleType.value === 'van' ? 1.2 : 0.8
  const g = 9.81

  return apiData.value.segments_def.map((seg) => {
    const isToll = customTollFlags.value[seg.id] ?? false
    const len = seg.length_km
    let speed: number
    let tollFee = 0
    let timeH: number
    let fuel: number
    let wear: number
    let title: string

    if (isToll) {
      speed = isNight.value ? 83 : 110
      tollFee = isNight.value ? seg.toll_night : seg.toll_day
      if (vehicleType.value === 'van') tollFee = Math.round(tollFee * 1.5)
      const vMs = speed / 3.6
      timeH = len / speed
      const rho = isNight.value ? 1.28 : 1.18
      const effCda = isNight.value ? cda * 0.82 : cda
      const f = mass * g * crr + 0.5 * rho * effCda * (vMs ** 2)
      fuel = (f * len * 1000) / (eta * qFuel) + idleLph * timeH
      wear = 40
      title = seg.toll_name
    } else {
      speed = seg.bottleneck ? 52 : 80
      if (isNight.value) speed += 4
      const lenEff = seg.bottleneck ? len * 1.05 : len
      const vMs = speed / 3.6
      timeH = lenEff / speed
      const rho = isNight.value ? 1.28 : 1.18
      const f = mass * g * crr + 0.5 * rho * cda * (vMs ** 2)
      const fuelDrive = (f * lenEff * 1000) / (eta * qFuel) + idleLph * timeH * (seg.bottleneck ? 1.3 : 1.0)
      let cycles = seg.bottleneck ? Math.round(len * 0.3) : Math.round(len * 0.04)
      if (isNight.value) cycles = Math.max(1, Math.round(cycles * 0.25))
      const dek = cycles * 0.5 * mass * ((75 / 3.6) ** 2 - (30 / 3.6) ** 2)
      fuel = fuelDrive + dek / (eta * qFuel)
      tollFee = 0
      wear = seg.bottleneck ? 220 : 50
      title = seg.free_name
    }

    return {
      id: seg.id,
      name: seg.name,
      title,
      from_km: seg.from_km,
      to_km: seg.to_km,
      length_km: len,
      is_toll: isToll,
      speed_kmh: Math.round(speed * 10) / 10,
      duration_min: Math.round(timeH * 60 * 10) / 10,
      fuel_liters: Math.round(fuel * 100) / 100,
      fuel_per_100km: Math.round((fuel / len) * 100 * 100) / 100,
      toll_rub: tollFee,
      wear_rub: wear,
      fuel_cost_rub: Math.round(fuel * fuelPrice.value),
    }
  })
})
const routeTotals = computed(() => {
  const segs = currentSegments.value
  const dist = segs.reduce((sum, s) => sum + s.length_km, 0)
  const timeMin = segs.reduce((sum, s) => sum + s.duration_min, 0)
  const fuel = segs.reduce((sum, s) => sum + s.fuel_liters, 0)
  const toll = segs.reduce((sum, s) => sum + s.toll_rub, 0)
  const wear = segs.reduce((sum, s) => sum + s.wear_rub, 0)
  const fuelCost = Math.round(fuel * fuelPrice.value)
  const timeH = timeMin / 60
  const timeCost = Math.round(timeH * valueOfTime.value)
  const totalCost = fuelCost + toll + wear + timeCost
  const avgSpeed = dist > 0 && timeH > 0 ? Math.round((dist / timeH) * 10) / 10 : 0
  const per100 = dist > 0 ? Math.round((fuel / dist) * 100 * 100) / 100 : 0

  return { dist, timeMin, timeH, fuel, toll, wear, fuelCost, timeCost, totalCost, avgSpeed, per100 }
})

watch(currentSegments, (segs) => {
  emit('update:segments', segs)
}, { immediate: true })
const simDistance = ref(0)
const simPlaying = ref(false)
const simSpeedMultiplier = ref(20)
let simTimer: number | undefined

const totalRouteKm = 465.0
const currentActiveSegment = computed(() => {
  const km = simDistance.value
  return currentSegments.value.find((s) => km >= s.from_km && km < s.to_km) ?? currentSegments.value.at(-1)
})
const simAccumulatedFuel = computed(() => {
  const km = simDistance.value
  let acc = 0
  for (const seg of currentSegments.value) {
    if (km >= seg.to_km) {
      acc += seg.fuel_liters
    } else if (km > seg.from_km) {
      const part = (km - seg.from_km) / seg.length_km
      acc += seg.fuel_liters * part
      break
    }
  }
  return Math.round(acc * 100) / 100
})

function startSimulation() {
  if (simDistance.value >= totalRouteKm) {
    simDistance.value = 0
  }
  simPlaying.value = true
  lastTick = performance.now()
  runSimLoop()
}

function pauseSimulation() {
  simPlaying.value = false
  if (simTimer !== undefined) {
    cancelAnimationFrame(simTimer)
    simTimer = undefined
  }
}

function resetSimulation() {
  pauseSimulation()
  simDistance.value = 0
  syncMap(0)
}

let lastTick = 0
function runSimLoop() {
  if (!simPlaying.value) return
  const now = performance.now()
  const dt = (now - lastTick) / 1000
  lastTick = now
  const currentSpeed = currentActiveSegment.value?.speed_kmh ?? 80
  const deltaKm = (currentSpeed / 3600) * dt * simSpeedMultiplier.value

  simDistance.value = Math.min(totalRouteKm, simDistance.value + deltaKm)
  syncMap(simDistance.value)

  if (simDistance.value >= totalRouteKm) {
    simPlaying.value = false
  } else {
    simTimer = requestAnimationFrame(runSimLoop)
  }
}

function onSliderSeek(e: Event) {
  const val = Number((e.target as HTMLInputElement).value)
  simDistance.value = val
  syncMap(val)
}

function jumpToSegment(seg: RouteSegment) {
  simDistance.value = seg.from_km
  syncMap(seg.from_km)
}

function syncMap(km: number) {
  if (!props.playback) return
  const dur = props.playback.tripDuration
  if (dur > 0) {
    const fraction = km / totalRouteKm
    props.playback.seek(fraction * dur)
  }
}

onBeforeUnmount(() => {
  if (simTimer !== undefined) cancelAnimationFrame(simTimer)
})

const chartMaxFuel = computed(() => (vehicleType.value === 'van' ? 80 : 32))
const maxSegmentPer100 = computed(() => (vehicleType.value === 'van' ? 18 : 7.5))

function buildFuelPath(segments?: RouteSegment[]): string {
  if (!segments?.length) return 'M 30,120 L 360,120'
  const maxF = chartMaxFuel.value
  let acc = 0
  const pts = ['30,120']
  for (const s of segments) {
    acc += s.fuel_liters
    const x = 30 + (s.to_km / totalRouteKm) * 330
    const y = 120 - (acc / maxF) * 100
    pts.push(`${x.toFixed(1)},${y.toFixed(1)}`)
  }
  return `M ${pts.join(' L ')}`
}

function formatTimeH(hours: number): string {
  const h = Math.floor(hours)
  const m = Math.round((hours - h) * 60)
  return `${h} ч ${m.toString().padStart(2, '0')} мин`
}

function formatRub(val: number): string {
  return val.toLocaleString('ru-RU') + ' ₽'
}
</script>

<template>
  <div class="optimizer-panel">
    <header class="side-section opt-header">
      <span class="section-kicker">ЛАБОРАТОРНАЯ РАБОТА №2</span>
      <h2>Интеллектуальный выбор маршрута и времени</h2>
      <p>
        Интерактивный симулятор: переключайте участки между платными и бесплатными, меняйте время старта и смотрите расход топлива на каждом отрезке.
      </p>
      <div class="opt-controls">
        <div class="control-row">
          <label class="control-label">Тип автомобиля</label>
          <div class="vehicle-toggle">
            <button
              type="button"
              :class="{ active: vehicleType === 'car' }"
              @click="vehicleType = 'car'"
            >
              🚗 Легковой (1650 кг)
            </button>
            <button
              type="button"
              :class="{ active: vehicleType === 'van' }"
              @click="vehicleType = 'van'"
            >
              🚐 Фургон (2800 кг)
            </button>
          </div>
        </div>

        <div class="sliders-row">
          <div class="slider-box">
            <div class="slider-header">
              <span>Топливо:</span>
              <strong>{{ fuelPrice }} ₽/л</strong>
            </div>
            <input
              v-model.number="fuelPrice"
              type="range"
              min="50"
              max="95"
              step="1"
              class="point-slider"
            />
          </div>

          <div class="slider-box">
            <div class="slider-header">
              <span>Ценность часа:</span>
              <strong>{{ valueOfTime }} ₽/ч</strong>
            </div>
            <input
              v-model.number="valueOfTime"
              type="range"
              min="200"
              max="1500"
              step="50"
              class="point-slider"
            />
          </div>
        </div>
      </div>
    </header>
    <div class="side-section preset-selector">
      <div class="section-heading">
        <span class="gauge-label">ГОТОВЫЕ ВАРИАНТЫ ДВИЖЕНИЯ</span>
        <span class="file-tag">Москва → Липецк</span>
      </div>

      <div class="preset-buttons">
        <button
          type="button"
          class="preset-btn"
          :class="{ active: activePreset === 'toll' }"
          @click="selectPreset('toll')"
        >
          <span class="p-title">1. Платная М-4</span>
          <span class="p-sub">110 км/ч · День 10:00</span>
        </button>

        <button
          type="button"
          class="preset-btn"
          :class="{ active: activePreset === 'free' }"
          @click="selectPreset('free')"
        >
          <span class="p-title">2. Через деревни</span>
          <span class="p-sub">Бесплатно · 58 н.п.</span>
        </button>

        <button
          type="button"
          class="preset-btn p-best"
          :class="{ active: activePreset === 'hybrid' }"
          @click="selectPreset('hybrid')"
        >
          <span class="p-badge">Выгодно</span>
          <span class="p-title">3. Умный Гибрид</span>
          <span class="p-sub">83 км/ч · Ночь 23:30</span>
        </button>
      </div>
      <div class="time-toggle-row">
        <span>Время старта:</span>
        <button
          type="button"
          class="time-btn"
          :class="{ active: !isNight }"
          @click="isNight = false"
        >
          ☀️ День (10:00)
        </button>
        <button
          type="button"
          class="time-btn"
          :class="{ active: isNight }"
          @click="isNight = true"
        >
          🌙 Ночь (23:30, дешевый тариф)
        </button>
      </div>
    </div>
    <div class="side-section sim-player">
      <div class="sim-header">
        <span class="gauge-label">СИМУЛЯТОР ПОЕЗДКИ ПО КАРТЕ</span>
        <div class="sim-speed-controls">
          <span>Скорость:</span>
          <button
            type="button"
            :class="{ active: simSpeedMultiplier === 10 }"
            @click="simSpeedMultiplier = 10"
          >
            10x
          </button>
          <button
            type="button"
            :class="{ active: simSpeedMultiplier === 30 }"
            @click="simSpeedMultiplier = 30"
          >
            30x
          </button>
          <button
            type="button"
            :class="{ active: simSpeedMultiplier === 80 }"
            @click="simSpeedMultiplier = 80"
          >
            80x
          </button>
        </div>
      </div>
      <div class="sim-controls-bar">
        <button
          v-if="!simPlaying"
          type="button"
          class="sim-btn sim-play-btn"
          @click="startSimulation"
        >
          ▶ Проехать маршрут
        </button>
        <button
          v-else
          type="button"
          class="sim-btn sim-pause-btn"
          @click="pauseSimulation"
        >
          ⏸ Пауза
        </button>
        <button type="button" class="sim-btn sim-reset-btn" @click="resetSimulation">
          ↺ Сброс
        </button>

        <span class="sim-km-label">{{ Math.round(simDistance) }} / 465 км</span>
      </div>
      <input
        type="range"
        min="0"
        max="465"
        step="1"
        :value="simDistance"
        class="point-slider sim-slider"
        @input="onSliderSeek"
      />
      <div class="sim-live-card">
        <div class="live-item">
          <span class="l-label">Текущий отрезок</span>
          <strong class="l-val">{{ currentActiveSegment?.name }}</strong>
          <small>{{ currentActiveSegment?.title }}</small>
        </div>

        <div class="live-grid">
          <div>
            <span>Скорость:</span>
            <strong>{{ currentActiveSegment?.speed_kmh }} км/ч</strong>
          </div>
          <div>
            <span>Сожжено бензина:</span>
            <strong class="fuel-burn">{{ simAccumulatedFuel }} л</strong>
          </div>
          <div>
            <span>Режим участка:</span>
            <strong :class="currentActiveSegment?.is_toll ? 'tag-toll' : 'tag-free'">
              {{ currentActiveSegment?.is_toll ? 'Платный' : 'Бесплатный' }}
            </strong>
          </div>
        </div>
      </div>
    </div>
    <div class="side-section route-summary-card">
      <div class="summary-top">
        <div>
          <span class="section-kicker">ИТОГ ПО ТЕКУЩЕМУ МАРШРУТУ</span>
          <h3>{{ formatRub(routeTotals.totalCost) }}</h3>
        </div>
        <div class="summary-time-badge">
          {{ formatTimeH(routeTotals.timeH) }}
        </div>
      </div>

      <div class="summary-metrics-row">
        <div>
          <span>Всего бензина:</span>
          <strong>{{ routeTotals.fuel.toFixed(1) }} л</strong>
          <small>{{ routeTotals.per100 }} л / 100 км</small>
        </div>
        <div>
          <span>Бензин:</span>
          <strong>{{ formatRub(routeTotals.fuelCost) }}</strong>
        </div>
        <div>
          <span>Платные дороги:</span>
          <strong>{{ formatRub(routeTotals.toll) }}</strong>
        </div>
        <div>
          <span>Износ + Время:</span>
          <strong>{{ formatRub(routeTotals.wear + routeTotals.timeCost) }}</strong>
        </div>
      </div>
    </div>
    <div class="side-section segment-bars-section">
      <div class="section-heading">
        <span class="gauge-label">РАСХОД ТОПЛИВА ПО 6 УЧАСТКАМ</span>
        <small class="legend-note">Кликните [Платно]/[Бесплатно] для смены режима</small>
      </div>

      <div class="segments-list">
        <div
          v-for="seg in currentSegments"
          :key="seg.id"
          class="segment-row-card"
          :class="{
            'active-segment': currentActiveSegment?.id === seg.id,
            'is-toll-seg': seg.is_toll,
          }"
        >
          <div class="seg-top">
            <div class="seg-info">
              <span class="seg-num">Участок {{ seg.id }} · {{ seg.length_km }} км</span>
              <strong>{{ seg.name }}</strong>
              <span class="seg-sub">{{ seg.title }}</span>
            </div>
            <div class="seg-actions">
              <button
                type="button"
                class="seg-toggle-btn"
                :class="seg.is_toll ? 'btn-toll' : 'btn-free'"
                @click="toggleSegment(seg.id)"
              >
                {{ seg.is_toll ? '💳 Платно' : '🆓 Бесплатно' }}
              </button>
              <button
                type="button"
                class="seg-map-pin"
                title="Показать на карте"
                @click="jumpToSegment(seg)"
              >
                📍
              </button>
            </div>
          </div>
          <div class="seg-metrics-line">
            <span>{{ seg.speed_kmh }} км/ч · {{ seg.duration_min }} мин</span>
            <span v-if="seg.toll_rub > 0" class="seg-toll-fee">+{{ seg.toll_rub }} ₽</span>
            <strong class="seg-fuel-liters">{{ seg.fuel_liters }} л</strong>
            <span class="seg-per-hundred">({{ seg.fuel_per_100km }} л/100км)</span>
          </div>
          <div class="fuel-bar-track">
            <div
              class="fuel-bar-fill"
              :class="
                seg.fuel_per_100km > (vehicleType === 'van' ? 14.0 : 6.0)
                  ? 'bar-red'
                  : seg.fuel_per_100km > (vehicleType === 'van' ? 10.5 : 4.8)
                  ? 'bar-yellow'
                  : 'bar-green'
              "
              :style="{ width: Math.min(100, (seg.fuel_per_100km / maxSegmentPer100) * 100) + '%' }"
            />
          </div>
        </div>
      </div>
    </div>
    <div class="side-section cumulative-chart-section">
      <div class="section-heading">
        <span class="gauge-label">НАКОПЛЕННЫЙ РАСХОД ТОПЛИВА (0–465 КМ)</span>
      </div>

      <div class="chart-box">
        <svg viewBox="0 0 380 140" class="cumulative-svg">
          <line x1="30" y1="20" x2="360" y2="20" stroke="#e7e5dc" stroke-width="1" />
          <line x1="30" y1="60" x2="360" y2="60" stroke="#e7e5dc" stroke-width="1" />
          <line x1="30" y1="100" x2="360" y2="100" stroke="#e7e5dc" stroke-width="1" />
          <text x="24" y="23" class="svg-axis">{{ Math.round(chartMaxFuel) }}л</text>
          <text x="24" y="63" class="svg-axis">{{ Math.round(chartMaxFuel * 0.6) }}л</text>
          <text x="24" y="103" class="svg-axis">{{ Math.round(chartMaxFuel * 0.2) }}л</text>
          <text x="24" y="125" class="svg-axis">0л</text>
          <path
            :d="buildFuelPath(apiData?.variants[0]?.segments)"
            fill="none"
            stroke="#d45b5b"
            stroke-width="2"
            stroke-dasharray="3 3"
          />
          <path
            :d="buildFuelPath(apiData?.variants[1]?.segments)"
            fill="none"
            stroke="#d9822b"
            stroke-width="2"
          />
          <path
            :d="buildFuelPath(apiData?.variants[2]?.segments)"
            fill="none"
            stroke="#2b8a4b"
            stroke-width="2.5"
          />
          <line
            :x1="30 + (simDistance / 465) * 330"
            y1="10"
            :x2="30 + (simDistance / 465) * 330"
            y2="120"
            stroke="#1b4d2e"
            stroke-width="1.5"
            stroke-dasharray="2 2"
          />
          <circle
            :cx="30 + (simDistance / 465) * 330"
            :cy="120 - (simAccumulatedFuel / chartMaxFuel) * 100"
            r="4"
            fill="#1b4d2e"
          />
          <text x="30" y="134" class="svg-axis">0</text>
          <text x="151" y="134" class="svg-axis">170 км</text>
          <text x="265" y="134" class="svg-axis">330 км</text>
          <text x="345" y="134" class="svg-axis">465 км</text>
        </svg>

        <div class="chart-legend-box">
          <span class="leg-item"><i class="leg-red" /> 1. Платная ({{ apiData?.variants[0]?.fuel_liters ?? 30.4 }} л)</span>
          <span class="leg-item"><i class="leg-orange" /> 2. Деревни ({{ apiData?.variants[1]?.fuel_liters ?? 24.7 }} л)</span>
          <span class="leg-item"><i class="leg-green" /> 3. Гибрид ({{ apiData?.variants[2]?.fuel_liters ?? 22.7 }} л)</span>
        </div>
      </div>
    </div>
    <div class="side-section methodology-notes">
      <span class="section-kicker">ОБОСНОВАНИЕ МЕТОДИКИ</span>
      <h3>Почему это работает лучше всего</h3>
      <div class="notes-grid">
        <div class="note-box">
          <strong>💨 Скорость vs Воздух</strong>
          <p>
            На 110 км/ч аэродинамика сжигает на 25% больше бензина, а плата за проезд М-4 превышает стоимость всего топлива.
          </p>
        </div>
        <div class="note-box">
          <strong>🛑 Деревни vs Тормоза</strong>
          <p>
            На бесплатной дороге 58 населенных пунктов и камер: постоянные торможения убивают колодки и ~8 часов времени.
          </p>
        </div>
        <div class="note-box">
          <strong>🔀 Чередование участков</strong>
          <p>
            Платим только за объезд 3 узких мест (Москва, Богородицк, Елец). Длинные прямики едем бесплатно на 80–85 км/ч.
          </p>
        </div>
        <div class="note-box">
          <strong>🌙 Ночной старт (23:30)</strong>
          <p>
            Дешевый ночной тариф «Автодор», свободные дороги без пешеходных светофоров и равномерный темп без остановок.
          </p>
        </div>
      </div>
      <p class="sources-line">
        <strong>Источники:</strong> модель тяги (Чудаков Е. А., Гришкевич А. И.), методика Value of Time (Минтранс РФ), тарифы ГК «Автодор» (М-4 «Дон»), исследования SAE/NREL.
      </p>
    </div>
  </div>
</template>

<style scoped>
.optimizer-panel {
  display: flex;
  flex-direction: column;
}

.opt-header h2 {
  margin: 6px 0 8px;
  color: var(--ink);
  font-size: 19px;
  line-height: 1.2;
}

.opt-header p {
  margin: 0 0 14px;
  color: var(--muted);
  font-size: 11px;
  line-height: 1.5;
}

.opt-controls {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 11px;
  border: 1px solid #e8e5da;
  border-radius: 12px;
  background: #f7f6f0;
}

.control-label {
  display: block;
  margin-bottom: 5px;
  color: #798379;
  font-size: 9.5px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.vehicle-toggle {
  display: flex;
  gap: 6px;
}

.vehicle-toggle button {
  flex: 1;
  padding: 7px 6px;
  border: 1px solid #dddcd1;
  border-radius: 8px;
  background: #fffefa;
  color: #4b5a4f;
  font-size: 10.5px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.16s ease;
}

.vehicle-toggle button.active {
  border-color: var(--forest);
  background: var(--forest);
  color: #fbfaf5;
}

.sliders-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.slider-box {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.slider-header {
  display: flex;
  justify-content: space-between;
  color: #637064;
  font-size: 9.5px;
}

.slider-header strong {
  color: var(--forest);
  font-weight: 700;
}
.preset-buttons {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 6px;
  margin-top: 8px;
}

.preset-btn {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 9px 5px;
  border: 1px solid #dedcd0;
  border-radius: 8px;
  background: #fffefa;
  cursor: pointer;
  text-align: center;
  transition: all 0.16s ease;
}

.preset-btn.active {
  border-color: var(--forest);
  background: #eef3ee;
  box-shadow: 0 2px 8px #26352e15;
}

.p-title {
  color: #27372c;
  font-size: 11px;
  font-weight: 700;
}

.p-sub {
  color: #7b857c;
  font-size: 8.5px;
  margin-top: 2px;
}

.p-badge {
  position: absolute;
  top: -6px;
  right: 6px;
  padding: 1px 5px;
  border-radius: 4px;
  background: #1b632c;
  color: #fff;
  font-size: 7.5px;
  font-weight: 800;
  text-transform: uppercase;
}

.time-toggle-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  font-size: 10.5px;
  color: #5d695e;
}

.time-btn {
  padding: 5px 8px;
  border: 1px solid #dcd9cc;
  border-radius: 6px;
  background: #fff;
  color: #556257;
  font-size: 10px;
  cursor: pointer;
}

.time-btn.active {
  border-color: #2e543c;
  background: #2e543c;
  color: #fff;
  font-weight: 700;
}
.sim-player {
  background: #fbfbf6;
  border-left: 3px solid #346146;
}

.sim-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.sim-speed-controls {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 9.5px;
  color: #7b877c;
}

.sim-speed-controls button {
  padding: 2px 6px;
  border: 1px solid #d8d6c8;
  border-radius: 4px;
  background: #fff;
  font-size: 9px;
  cursor: pointer;
}

.sim-speed-controls button.active {
  background: var(--forest);
  color: #fff;
  border-color: var(--forest);
}

.sim-controls-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.sim-btn {
  padding: 7px 12px;
  border-radius: 7px;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  border: none;
  transition: all 0.16s ease;
}

.sim-play-btn {
  background: var(--forest);
  color: #fff;
}

.sim-play-btn:hover {
  background: #234d34;
}

.sim-pause-btn {
  background: #c97126;
  color: #fff;
}

.sim-reset-btn {
  background: #eae8dd;
  color: #4a574c;
}

.sim-km-label {
  margin-left: auto;
  color: #3b4e40;
  font-size: 11px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.sim-slider {
  margin: 6px 0 10px;
}

.sim-live-card {
  padding: 9px 11px;
  border: 1px solid #e5e3d7;
  border-radius: 9px;
  background: #fff;
}

.live-item {
  display: flex;
  flex-direction: column;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px dashed #e8e6dc;
}

.l-label {
  color: #8c978d;
  font-size: 8.5px;
  text-transform: uppercase;
}

.l-val {
  color: #213225;
  font-size: 12.5px;
}

.live-item small {
  color: #6a776c;
  font-size: 9.5px;
}

.live-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 6px;
  font-size: 10px;
}

.live-grid div {
  display: flex;
  flex-direction: column;
}

.live-grid span {
  color: #8c968d;
  font-size: 8.5px;
}

.live-grid strong {
  color: #2e3e32;
  font-size: 11.5px;
}

.fuel-burn {
  color: #1a632e !important;
}

.tag-toll {
  color: #1a632e;
}

.tag-free {
  color: #a06427;
}
.route-summary-card {
  background: #eef4ee;
  border-left: 4px solid var(--forest);
}

.summary-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.summary-top h3 {
  margin: 2px 0 0;
  color: #1c4b27;
  font-size: 22px;
}

.summary-time-badge {
  padding: 4px 8px;
  border-radius: 6px;
  background: #fff;
  border: 1px solid #c9d8cb;
  color: #275233;
  font-size: 11px;
  font-weight: 700;
}

.summary-metrics-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr;
  gap: 6px;
  padding-top: 8px;
  border-top: 1px dashed #cbdbce;
}

.summary-metrics-row div {
  display: flex;
  flex-direction: column;
}

.summary-metrics-row span {
  color: #657768;
  font-size: 8.5px;
}

.summary-metrics-row strong {
  color: #223727;
  font-size: 12px;
}

.summary-metrics-row small {
  color: #4b664f;
  font-size: 8.5px;
}
.segments-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
}

.segment-row-card {
  padding: 10px 11px;
  border: 1px solid #e7e5dc;
  border-radius: 9px;
  background: #fffefa;
  transition: all 0.16s ease;
}

.segment-row-card.active-segment {
  border-color: #2b7040;
  box-shadow: 0 2px 10px #2b704020;
  background: #fbfdfb;
}

.seg-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}

.seg-info {
  display: flex;
  flex-direction: column;
}

.seg-num {
  color: #8c7662;
  font-size: 8.5px;
  font-weight: 700;
}

.seg-info strong {
  color: #2a3a2e;
  font-size: 12px;
}

.seg-sub {
  color: #6e7a70;
  font-size: 9.5px;
}

.seg-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.seg-toggle-btn {
  padding: 4px 7px;
  border-radius: 6px;
  font-size: 9.5px;
  font-weight: 700;
  cursor: pointer;
  border: 1px solid transparent;
}

.btn-toll {
  background: #e3efe5;
  color: #1e5c2b;
  border-color: #b7d6bd;
}

.btn-free {
  background: #fbf2e7;
  color: #a45a1f;
  border-color: #edd1b7;
}

.seg-map-pin {
  padding: 3px 5px;
  border: 1px solid #dddcd2;
  border-radius: 5px;
  background: #fff;
  cursor: pointer;
  font-size: 11px;
}

.seg-metrics-line {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin: 6px 0 4px;
  font-size: 10px;
  color: #6c796e;
}

.seg-toll-fee {
  padding: 1px 4px;
  border-radius: 4px;
  background: #e9ece4;
  color: #3b5a41;
  font-weight: 600;
  font-size: 9px;
}

.seg-fuel-liters {
  margin-left: auto;
  color: #243528;
  font-size: 12px;
}

.seg-per-hundred {
  color: #7b887d;
  font-size: 9px;
}

.fuel-bar-track {
  height: 5px;
  background: #ece9df;
  border-radius: 4px;
  overflow: hidden;
}

.fuel-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.bar-green {
  background: #2fa155;
}

.bar-yellow {
  background: #dba232;
}

.bar-red {
  background: #db4949;
}
.chart-box {
  margin-top: 8px;
  padding: 10px;
  border: 1px solid #e7e5dc;
  border-radius: 10px;
  background: #fffefa;
}

.cumulative-svg {
  width: 100%;
  height: auto;
  display: block;
}

.svg-axis {
  fill: #8b958c;
  font-size: 8px;
  font-family: sans-serif;
}

.chart-legend-box {
  display: flex;
  justify-content: space-between;
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px dashed #e6e4d8;
  font-size: 8.5px;
  color: #6c796e;
}

.leg-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.leg-item i {
  display: inline-block;
  width: 10px;
  height: 2px;
  border-radius: 2px;
}

.leg-red {
  background: #d45b5b;
}

.leg-orange {
  background: #d9822b;
}

.leg-green {
  background: #2b8a4b;
}

.legend-note {
  color: #8c978d;
  font-size: 8.5px;
}
.notes-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-top: 8px;
}

.note-box {
  padding: 8px 9px;
  border: 1px solid #e6e4d8;
  border-radius: 8px;
  background: #fbfbf6;
}

.note-box strong {
  display: block;
  color: #27372b;
  font-size: 10.5px;
  margin-bottom: 2px;
}

.note-box p {
  margin: 0;
  color: #647165;
  font-size: 9px;
  line-height: 1.4;
}

.sources-line {
  margin: 10px 0 0;
  padding-top: 8px;
  border-top: 1px dashed #e2dfd4;
  color: #6f7c70;
  font-size: 9px;
  line-height: 1.45;
}
</style>
