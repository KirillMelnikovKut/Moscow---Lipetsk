import type { ChartPoint } from '../types/domain'

export function sampleSeriesPath(
  points: ChartPoint[],
  min: number,
  max: number,
  x: (distance: number) => number,
  y: (value: number, min: number, max: number) => number,
  bottom: number,
  closeToBottom = false,
): string {
  if (points.length < 2) return ''
  const stride = Math.max(1, Math.ceil(points.length / 240))
  const indices: number[] = []
  for (let index = 0; index < points.length; index += stride) indices.push(index)
  if (indices.at(-1) !== points.length - 1) indices.push(points.length - 1)

  const path = indices.map((index, position) => {
    const point = points[index]
    return `${position ? 'L' : 'M'}${x(point.distance).toFixed(1)},${y(point.value, min, max).toFixed(1)}`
  }).join(' ')
  if (!closeToBottom) return path

  const first = points[indices[0]]
  const last = points[indices.at(-1)!]
  return `${path} L${x(last.distance).toFixed(1)},${bottom} L${x(first.distance).toFixed(1)},${bottom} Z`
}

export function floorIndex<T extends Record<K, number>, K extends keyof T>(items: T[], value: number, key: K): number {
  if (!items.length) return 0
  let low = 0
  let high = items.length - 1
  while (low < high) {
    const middle = Math.ceil((low + high) / 2)
    if (items[middle][key] <= value) low = middle
    else high = middle - 1
  }
  return low
}

export function mix(start: number, end: number, ratio: number): number {
  return start + (end - start) * ratio
}
