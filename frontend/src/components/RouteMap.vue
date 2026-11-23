<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as maplibregl from 'maplibre-gl'
import type { GeoJSONSource, StyleSpecification } from 'maplibre-gl'
import type { Feature, FeatureCollection, LineString } from 'geojson'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import type { ActiveTab, RouteSegment, TerrainPoint } from '../types/domain'
import { formatNumber } from '../utils/format'

maplibregl.setWorkerUrl(workerUrl)

const props = defineProps<{
  route: TerrainPoint[]
  routeDistance: number
  currentDistance: number
  terrainIndex: number
  coordinate: [number, number]
  activeTab?: ActiveTab
  routeSegments?: RouteSegment[]
}>()

const mapElement = ref<HTMLDivElement | null>(null)
let map: maplibregl.Map | null = null
let marker: maplibregl.Marker | null = null
let progressTimer: number | undefined
let lastProgressDraw = 0

const FREE_DETOUR_WAYPOINTS: Record<number, number[][]> = {
  1: [
    [37.6723, 55.5954],
    [37.7660, 55.4370],
    [37.8820, 55.2650],
    [37.9550, 55.1250],
    [38.0750, 54.8920],
    [37.9567, 55.0041],
  ],
  2: [
    [37.9567, 55.0041],
    [38.2450, 54.8050],
    [38.2480, 54.5150],
    [38.2680, 54.3480],
    [38.1547, 54.3542],
  ],
  3: [
    [38.1547, 54.3542],
    [38.1600, 53.9780],
    [38.1320, 53.7720],
    [38.1021, 53.5994],
  ],
  4: [
    [38.1021, 53.5994],
    [38.2850, 53.4350],
    [38.1180, 53.1520],
    [38.2205, 53.0062],
  ],
  5: [
    [38.2205, 53.0062],
    [38.3520, 52.7600],
    [38.4960, 52.6240],
    [38.9187, 52.5783],
  ],
}

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

function collectionData(lines: number[][][]): FeatureCollection<LineString> {
  return {
    type: 'FeatureCollection',
    features: lines.filter(c => c.length > 1).map(c => lineData(c)),
  }
}

function getHighwaySlice(fromKm: number, toKm: number): number[][] {
  const fromM = fromKm * 1000
  const toM = toKm * 1000
  const pts = props.route.filter(p => p.distance >= fromM && p.distance <= toM)
  if (pts.length < 2) return []
  const step = Math.max(1, Math.floor(pts.length / 80))
  const coords: number[][] = []
  for (let i = 0; i < pts.length; i += step) {
    coords.push([pts[i].lon, pts[i].lat])
  }
  const last = pts[pts.length - 1]
  coords.push([last.lon, last.lat])
  return coords
}

function updateSegmentLayers() {
  if (!map?.isStyleLoaded() || props.route.length < 2) return

  const isRoutesMode = props.activeTab === 'routes' && (props.routeSegments?.length ?? 0) > 0
  const tollLines: number[][][] = []
  const freeLines: number[][][] = []
  const altLines: number[][][] = []

  if (isRoutesMode && props.routeSegments) {
    for (const seg of props.routeSegments) {
      const highwayCoords = getHighwaySlice(seg.from_km, seg.to_km)
      const detourCoords = FREE_DETOUR_WAYPOINTS[seg.id] ?? highwayCoords

      if (seg.is_toll) {
        if (highwayCoords.length > 1) tollLines.push(highwayCoords)
        if (FREE_DETOUR_WAYPOINTS[seg.id]) altLines.push(detourCoords)
      } else {
        freeLines.push(detourCoords)
        if (FREE_DETOUR_WAYPOINTS[seg.id] && highwayCoords.length > 1) altLines.push(highwayCoords)
      }
    }
  }

  ;(map.getSource('segments-alt') as GeoJSONSource | undefined)?.setData(collectionData(altLines))
  ;(map.getSource('segments-toll') as GeoJSONSource | undefined)?.setData(collectionData(tollLines))
  ;(map.getSource('segments-free') as GeoJSONSource | undefined)?.setData(collectionData(freeLines))

  if (map.getLayer('route-main')) {
    map.setLayoutProperty('route-main', 'visibility', isRoutesMode ? 'none' : 'visible')
  }
  if (map.getLayer('traveled-main')) {
    map.setLayoutProperty('traveled-main', 'visibility', isRoutesMode ? 'none' : 'visible')
  }
  if (map.getLayer('segments-alt-layer')) {
    map.setLayoutProperty('segments-alt-layer', 'visibility', isRoutesMode ? 'visible' : 'none')
  }
  if (map.getLayer('segments-toll-layer')) {
    map.setLayoutProperty('segments-toll-layer', 'visibility', isRoutesMode ? 'visible' : 'none')
  }
  if (map.getLayer('segments-free-layer')) {
    map.setLayoutProperty('segments-free-layer', 'visibility', isRoutesMode ? 'visible' : 'none')
  }
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

    map.addSource('segments-alt', { type: 'geojson', data: collectionData([]) })
    map.addLayer({ id: 'segments-alt-layer', type: 'line', source: 'segments-alt',
      paint: { 'line-color': '#6b776e', 'line-width': 2.5, 'line-opacity': 0.55, 'line-dasharray': [2, 2] },
      layout: { 'line-cap': 'round', 'line-join': 'round', 'visibility': 'none' } })

    map.addSource('segments-toll', { type: 'geojson', data: collectionData([]) })
    map.addLayer({ id: 'segments-toll-layer', type: 'line', source: 'segments-toll',
      paint: { 'line-color': '#1d7a46', 'line-width': 5 },
      layout: { 'line-cap': 'round', 'line-join': 'round', 'visibility': 'none' } })

    map.addSource('segments-free', { type: 'geojson', data: collectionData([]) })
    map.addLayer({ id: 'segments-free-layer', type: 'line', source: 'segments-free',
      paint: { 'line-color': '#d97724', 'line-width': 5 },
      layout: { 'line-cap': 'round', 'line-join': 'round', 'visibility': 'none' } })
  }
  if (!marker) {
    const element = document.createElement('div')
    element.className = 'vehicle-marker'
    element.innerHTML = '<span>➤</span>'
    marker = new maplibregl.Marker({ element, anchor: 'center' }).setLngLat(props.coordinate).addTo(map)
  }
  updateSegmentLayers()
  drawProgress(true)
  if (fit) {
    const bounds = new maplibregl.LngLatBounds()
    props.route.forEach(point => bounds.extend([point.lon, point.lat]))
    map.fitBounds(bounds, { padding: 55, maxZoom: 12, duration: 550 })
  }
}

watch(() => props.route, () => renderRoute(true))
watch(() => [props.activeTab, props.routeSegments], () => updateSegmentLayers(), { deep: true })
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
    <div v-if="activeTab === 'routes'" class="map-legend">
      <span class="legend-line" style="background:#1d7a46"></span> Платная М-4
      <span class="legend-line" style="margin-left:6px;background:#d97724"></span> Бесплатная через н.п.
      <span class="legend-line" style="margin-left:6px;background:transparent;border-top:2px dashed #6b776e;height:0"></span> Альтернатива
    </div>
    <div v-else class="map-legend">
      <span class="legend-line"></span> Весь маршрут
      <span class="legend-line traveled"></span> Пройдено
    </div>
  </section>
</template>
