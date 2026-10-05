<script setup lang="ts">
import type { Analysis } from '../types/domain'
import { formatNumber, formatTime } from '../utils/format'
defineProps<{ speed: number | null; predictedSlope: number | null; analysis: Analysis | null }>()
</script>

<template>
  <section class="side-section recommendation-section">
    <div class="section-kicker">РЕКОМЕНДАЦИЯ</div>
    <div class="recommendation-value">{{ formatNumber(speed, 1) }} <span>км/ч</span></div>
    <p>Оптимальная скорость в текущей точке при прогнозном уклоне {{ formatNumber(predictedSlope, 2) }} %.</p>
    <div class="compare-grid">
      <div><span>Исходная поездка</span><strong>{{ formatNumber(analysis?.baseline.fuel_liters, 1) }} л</strong><small>{{ formatTime(analysis?.baseline.duration_seconds) }}</small></div>
      <div><span>Рекомендация</span><strong>{{ formatNumber(analysis?.optimal.fuel_liters, 1) }} л</strong><small>{{ formatTime(analysis?.optimal.duration_seconds) }}</small></div>
    </div>
    <p class="assumption">Модельный расход по сопротивлению качению, подъёму, воздуху и разгону. Ограничение времени: +10 %.</p>
  </section>
</template>
