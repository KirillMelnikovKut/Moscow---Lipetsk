<script setup lang="ts">
import type { TelemetryPoint } from '../types/domain'
import { formatNumber, formatTime } from '../utils/format'

defineProps<{ speed: number | null; engineRpm: number | null; rpmAngle: number; fuel: number | null; currentTelemetry: TelemetryPoint | null; playTime: number }>()
</script>

<template>
  <section class="side-section metric-section">
    <div class="section-heading"><span class="section-kicker">ПАНЕЛЬ ПРИБОРОВ</span><span class="file-tag">{{ currentTelemetry?.engine_rpm_estimated ? 'RPM · восстановлено' : 'RPM · исходные' }}</span></div>
    <div class="dashboard">
      <div class="speedometer"><span class="gauge-label">СКОРОСТЬ</span>
        <div class="speed-readout"><strong>{{ formatNumber(speed, 1) }}</strong><span>км/ч</span></div>
        <div class="gauge-track"><i :style="{ width: `${Math.min(100, (speed ?? 0) / 180 * 100)}%` }"></i></div>
        <div class="gauge-limits"><span>0</span><span>180</span></div>
      </div>
      <div class="tachometer"><svg viewBox="0 0 180 112" role="img" aria-label="Тахометр">
        <path d="M 20 93 A 70 70 0 0 1 160 93" class="tach-track" />
        <path d="M 20 93 A 70 70 0 0 1 160 93" class="tach-active" :style="{ strokeDasharray: `${Math.min(1, (engineRpm ?? 0) / 7000) * 220} 220` }" />
        <line x1="90" y1="92" x2="90" y2="31" class="tach-needle" :style="{ transform: `rotate(${rpmAngle}deg)` }" />
        <circle cx="90" cy="92" r="5" class="tach-hub" />
        <text x="90" y="72" class="tach-value">{{ formatNumber(engineRpm) }}</text><text x="90" y="87" class="tach-unit">об/мин</text>
        <text x="25" y="107" class="tach-limit">0</text><text x="148" y="107" class="tach-limit">7</text>
      </svg><span class="gauge-label">ОБОРОТЫ ДВИГАТЕЛЯ</span></div>
    </div>
    <div class="metric-grid">
      <div><span>Время в пути</span><strong>{{ formatTime(playTime) }}</strong></div>
      <div><span>Расход топлива</span><strong>{{ formatNumber(fuel, 2) }} л</strong></div>
      <div><span>Масса ТС</span><strong>{{ formatNumber(currentTelemetry?.vehicle_mass) }} кг</strong></div>
      <div><span>Масса груза</span><strong>{{ formatNumber(currentTelemetry?.cargo_mass) }} кг</strong></div>
    </div>
  </section>
</template>
