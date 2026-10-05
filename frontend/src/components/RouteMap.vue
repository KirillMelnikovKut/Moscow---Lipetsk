<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as maplibregl from 'maplibre-gl'
import type { GeoJSONSource, StyleSpecification } from 'maplibre-gl'
import type { Feature, LineString } from 'geojson'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import type { TerrainPoint } from '../types/domain'
import { formatNumber } from '../utils/format'

maplibregl.setWorkerUrl(workerUrl)

const props = defineProps<{
  route: TerrainPoint[]
  routeDistance: number
  currentDistance: number
  terrainIndex: number
  coordinate: [number, number]
}>()

const mapElement = ref<HTMLDivElement | null>(null)
let map: maplibregl.Map | null = null
let marker: maplibregl.Marker | null = null
let progressTimer: number | undefined
let lastProgressDraw = 0

const rasterStyle: StyleSpecification = {
  version: 8,
  sources: {
    'osm-tiles': {
      type: 'raster',
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      tileSize: 256,
      attribution: '© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap contributors</a>',
    },
  },
  layers: [{ id: 'osm-base', type: 'raster', source: 'osm-tiles' }],
}

function lineData(coordinates: number[][]): Feature<LineString> {
  const safeCoordinates = coordinates.length > 1 ? coordinates : [coordinates[0] ?? [0, 0], coordinates[0] ?? [0, 0]]
  return { type: 'Feature', properties: {}, geometry: { type: 'LineString', coordinates: safeCoordinates } }
}

function drawProgress(force = false) {
  if (!map || !marker || props.route.length === 0) return
  const now = performance.now()
  if (!force && now - lastProgressDraw < 90) {
    if (progressTimer === undefined) progressTimer = window.setTimeout(() => {
      progressTimer = undefined
      drawProgress(true)
    }, Math.max(1, 90 - (now - lastProgressDraw)))
    return
  }
  if (progressTimer !== undefined) {
    clearTimeout(progressTimer)
    progressTimer = undefined
  }
  lastProgressDraw = now
  marker.setLngLat(props.coordinate)
  const bearing = props.route[props.terrainIndex]?.bearing ?? 0
  const arrow = marker.getElement().firstElementChild as HTMLElement | null
  if (arrow) arrow.style.transform = `rotate(${bearing - 90}deg)`
  const travelled = props.route.slice(0, props.terrainIndex + 1).map(point => [point.lon, point.lat])
  travelled.push(props.coordinate)
  ;(map.getSource('traveled-line') as GeoJSONSource | undefined)?.setData(lineData(travelled))
}

function renderRoute(fit = false) {
  if (!map?.isStyleLoaded() || props.route.length < 2) return
  const coordinates = props.route.map(point => [point.lon, point.lat])
  const routeSource = map.getSource('route-line') as GeoJSONSource | undefined
  if (routeSource) routeSource.setData(lineData(coordinates))
  else {
    map.addSource('route-line', { type: 'geojson', data: lineData(coordinates) })
    map.addLayer({ id: 'route-shadow', type: 'line', source: 'route-line',
      paint: { 'line-color': '#263a30', 'line-width': 8, 'line-opacity': .16 },
      layout: { 'line-cap': 'round', 'line-join': 'round' } })
    map.addLayer({ id: 'route-main', type: 'line', source: 'route-line',
      paint: { 'line-color': '#557b68', 'line-width': 4 },
      layout: { 'line-cap': 'round', 'line-join': 'round' } })
    map.addSource('traveled-line', { type: 'geojson', data: lineData([coordinates[0]]) })
    map.addLayer({ id: 'traveled-main', type: 'line', source: 'traveled-line',
      paint: { 'line-color': '#d28d52', 'line-width': 4 },
      layout: { 'line-cap': 'round', 'line-join': 'round' } })
  }
  if (!marker) {
    const element = document.createElement('div')
    element.className = 'vehicle-marker'
    element.innerHTML = '<span>➤</span>'
    marker = new maplibregl.Marker({ element, anchor: 'center' }).setLngLat(props.coordinate).addTo(map)
  }
  drawProgress(true)
  if (fit) {
    const bounds = new maplibregl.LngLatBounds()
    props.route.forEach(point => bounds.extend([point.lon, point.lat]))
    map.fitBounds(bounds, { padding: 55, maxZoom: 12, duration: 550 })
  }
}

watch(() => props.route, () => renderRoute(true))
watch(() => [props.currentDistance, props.terrainIndex, props.coordinate[0], props.coordinate[1]], () => drawProgress())

onMounted(() => {
  if (!mapElement.value) return
  map = new maplibregl.Map({ container: mapElement.value, style: rasterStyle, center: [38.5, 54.3], zoom: 6 })
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')
  map.on('load', () => renderRoute(true))
})

onBeforeUnmount(() => {
  if (progressTimer !== undefined) clearTimeout(progressTimer)
  map?.remove()
})
</script>

<template>
  <section class="map-panel" aria-label="Карта маршрута">
    <div ref="mapElement" class="map-canvas"></div>
    <div class="map-title"><span class="map-title-kicker">МАРШРУТ</span><strong>Москва — Липецк</strong>
      <span>{{ formatNumber(routeDistance / 1000, 1) }} км · {{ formatNumber(route.length) }} точек</span>
    </div>
    <div class="map-legend"><span class="legend-line"></span> Весь маршрут <span class="legend-line traveled"></span> Пройдено</div>
  </section>
</template>
