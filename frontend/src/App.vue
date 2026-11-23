<script setup lang="ts">
import { ref } from 'vue'
import DataComparison from './components/DataComparison.vue'
import PanelTabs from './components/PanelTabs.vue'
import RouteMap from './components/RouteMap.vue'
import RouteOptimizer from './components/RouteOptimizer.vue'
import TripDashboard from './components/TripDashboard.vue'
import { useTripData } from './composables/useTripData'
import { useTripPlayback } from './composables/useTripPlayback'
import type { ActiveTab, RouteSegment } from './types/domain'

const { terrain, telemetry, analysis, comparison, terrainMessage, telemetryMessage, analysisMessage } = useTripData()
const playback = useTripPlayback(terrain, telemetry, analysis)
const activeTab = ref<ActiveTab>('dashboard')
const activeRouteSegments = ref<RouteSegment[]>([])
</script>

<template>
  <div class="app-shell">
    <main class="workspace">
      <RouteMap :route="terrain" :route-distance="playback.routeDistance" :current-distance="playback.currentDistance"
        :terrain-index="playback.terrainIndex" :coordinate="playback.coordinate"
        :active-tab="activeTab" :route-segments="activeRouteSegments" />
      <aside class="sidebar">
        <PanelTabs v-model="activeTab" />
        <TripDashboard v-if="activeTab === 'dashboard'" :terrain="terrain" :telemetry="telemetry" :analysis="analysis"
          :playback="playback" :terrain-message="terrainMessage" :telemetry-message="telemetryMessage"
          :analysis-message="analysisMessage" />
        <RouteOptimizer v-else-if="activeTab === 'routes'" :playback="playback" :terrain="terrain"
          @update:segments="activeRouteSegments = $event" />
        <DataComparison v-else :comparison="comparison" :analysis="analysis" />
      </aside>
    </main>
  </div>
</template>
