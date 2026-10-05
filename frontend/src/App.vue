<script setup lang="ts">
import { ref } from 'vue'
import DataComparison from './components/DataComparison.vue'
import PanelTabs from './components/PanelTabs.vue'
import RouteMap from './components/RouteMap.vue'
import TripDashboard from './components/TripDashboard.vue'
import { useTripData } from './composables/useTripData'
import { useTripPlayback } from './composables/useTripPlayback'
import type { ActiveTab } from './types/domain'

const { terrain, telemetry, analysis, comparison, terrainMessage, telemetryMessage, analysisMessage } = useTripData()
const playback = useTripPlayback(terrain, telemetry, analysis)
const activeTab = ref<ActiveTab>('dashboard')
</script>

<template>
  <div class="app-shell">
    <main class="workspace">
      <RouteMap :route="terrain" :route-distance="playback.routeDistance" :current-distance="playback.currentDistance"
        :terrain-index="playback.terrainIndex" :coordinate="playback.coordinate" />
      <aside class="sidebar">
        <PanelTabs v-model="activeTab" />
        <TripDashboard v-if="activeTab === 'dashboard'" :terrain="terrain" :telemetry="telemetry" :analysis="analysis"
          :playback="playback" :terrain-message="terrainMessage" :telemetry-message="telemetryMessage"
          :analysis-message="analysisMessage" />
        <DataComparison v-else :comparison="comparison" :analysis="analysis" />
      </aside>
    </main>
  </div>
</template>
