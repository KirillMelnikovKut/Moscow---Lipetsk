<script setup lang="ts">
import { formatNumber, formatTime } from '../utils/format'

defineProps<{
  playing: boolean; isFinished: boolean; hasTelemetry: boolean; playbackRate: number
  playTime: number; tripDuration: number; currentDistance: number; routeDistance: number; progress: number
}>()
const emit = defineEmits<{ toggle: []; reset: []; seek: [seconds: number]; 'rate-change': [rate: number] }>()
</script>

<template>
  <section class="side-section intro-section">
    <div class="section-kicker">ВОСПРОИЗВЕДЕНИЕ ПОЕЗДКИ</div><h2>Движение автомобиля</h2>
    <div class="play-controls">
      <button class="play-button" type="button" :disabled="!hasTelemetry" @click="emit('toggle')">{{ playing ? 'Пауза' : isFinished ? 'Повторить' : 'Старт' }}</button>
      <button type="button" :disabled="!hasTelemetry" @click="emit('reset')">Сброс</button>
      <label>Скорость <select :value="playbackRate" @change="emit('rate-change', Number(($event.target as HTMLSelectElement).value))">
        <option :value="1">×1</option><option :value="10">×10</option><option :value="100">×100</option><option :value="1000">×1000</option>
      </select></label>
    </div>
    <div class="progress-labels"><span>Москва</span><span>Липецк</span></div>
    <input class="point-slider" type="range" min="0" :max="tripDuration || 1" step="1" :value="playTime"
      :disabled="!hasTelemetry" aria-label="Время поездки"
      @input="emit('seek', Number(($event.target as HTMLInputElement).value))" />
    <div class="progress-position">{{ formatNumber(currentDistance / 1000, 1) }} / {{ formatNumber(routeDistance / 1000, 1) }} км · {{ formatNumber(progress * 100, 1) }} % <span v-if="playTime || tripDuration">· {{ formatTime(playTime) }} / {{ formatTime(tripDuration) }}</span></div>
  </section>
</template>
