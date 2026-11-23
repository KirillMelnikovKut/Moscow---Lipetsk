<script setup lang="ts">
import type { ActiveTab } from '../types/domain'
defineProps<{ modelValue: ActiveTab }>()
const emit = defineEmits<{ 'update:modelValue': [tab: ActiveTab] }>()
const tabs: { id: ActiveTab; label: string }[] = [
  { id: 'dashboard', label: 'Поездка' },
  { id: 'routes', label: 'Выбор маршрута' },
  { id: 'data', label: 'Данные' },
]
</script>

<template>
  <nav class="side-tabs" aria-label="Разделы панели">
    <button v-for="tab in tabs" :key="tab.id" type="button" :class="{ active: modelValue === tab.id }"
      :aria-current="modelValue === tab.id ? 'page' : undefined" @click="emit('update:modelValue', tab.id)">
      {{ tab.label }}
    </button>
  </nav>
</template>
