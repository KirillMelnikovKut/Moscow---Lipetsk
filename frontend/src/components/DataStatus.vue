<script setup lang="ts">
defineProps<{ terrainMessage: string; telemetryMessage: string; analysisMessage: string }>()
</script>

<template>
  <section class="side-section status-section">
    <div class="section-kicker">ИСТОЧНИКИ ДАННЫХ</div>
    <div class="status-line"><span class="status-icon"></span><span>{{ terrainMessage }}</span></div>
    <div class="status-line"><span class="status-icon"></span><span>{{ telemetryMessage }}</span></div>
    <div class="status-line"><span class="status-icon"></span><span>{{ analysisMessage }}</span></div>
    <p>Данные загружаются один раз при открытии страницы.</p>
  </section>
</template>
