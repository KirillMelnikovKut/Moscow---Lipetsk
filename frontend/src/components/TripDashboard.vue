<script setup lang="ts">
import DataStatus from './DataStatus.vue'
import InstrumentPanel from './InstrumentPanel.vue'
import PlaybackControls from './PlaybackControls.vue'
import RecommendationCard from './RecommendationCard.vue'
import RouteCharts from './RouteCharts.vue'
import type { TripPlaybackState } from '../composables/useTripPlayback'
import type { Analysis, TelemetryPoint, TerrainPoint } from '../types/domain'
import { formatNumber, formatTime } from '../utils/format'

defineProps<{
  terrain: TerrainPoint[]; telemetry: TelemetryPoint[]; analysis: Analysis | null
  playback: TripPlaybackState; terrainMessage: string; telemetryMessage: string; analysisMessage: string
}>()
</script>

<template>
  <PlaybackControls
    :playing="playback.playing" :is-finished="playback.isFinished" :has-telemetry="telemetry.length > 0"
    :playback-rate="playback.playbackRate" :play-time="playback.playTime" :trip-duration="playback.tripDuration"
    :current-distance="playback.currentDistance" :route-distance="playback.routeDistance" :progress="playback.progress"
    @toggle="playback.togglePlayback" @reset="playback.resetPlayback" @seek="playback.seek"
    @rate-change="playback.setPlaybackRate"
  />
  <InstrumentPanel :speed="playback.speed" :engine-rpm="playback.engineRpm" :rpm-angle="playback.rpmAngle"
    :fuel="playback.fuel" :current-telemetry="playback.currentTelemetry" :play-time="playback.playTime" />
  <RouteCharts :terrain="terrain" :telemetry="telemetry" :analysis="analysis" :current-distance="playback.currentDistance"
    :current-speed="playback.speed" :current-fuel="playback.fuel" :current-altitude="playback.currentTerrain?.altitude ?? null"
    :current-slope="playback.currentTerrain?.slope ?? null" />
  <RecommendationCard :speed="playback.optimalSpeed" :predicted-slope="playback.predictedSlope" :analysis="analysis" />
  <section v-if="playback.isFinished" class="side-section finish-section">
    <strong>Поездка завершена</strong>
    <span>{{ formatNumber(playback.routeDistance / 1000, 1) }} км · {{ formatTime(playback.tripDuration) }} · {{ formatNumber(analysis?.baseline.fuel_liters, 1) }} л</span>
  </section>
  <DataStatus :terrain-message="terrainMessage" :telemetry-message="telemetryMessage" :analysis-message="analysisMessage" />
</template>
