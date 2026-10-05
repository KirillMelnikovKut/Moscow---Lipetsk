export function formatNumber(value: number | null | undefined, digits = 0): string {
  return value == null || !Number.isFinite(value)
    ? '—'
    : value.toLocaleString('ru-RU', { maximumFractionDigits: digits })
}

export function formatTime(seconds: number | null | undefined): string {
  if (seconds == null || !Number.isFinite(seconds)) return '—'
  const rounded = Math.round(seconds)
  return [Math.floor(rounded / 3600), Math.floor((rounded % 3600) / 60), rounded % 60]
    .map(value => String(value).padStart(2, '0'))
    .join(':')
}
