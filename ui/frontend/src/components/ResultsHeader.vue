<template>
  <div class="flex flex-wrap items-center justify-between gap-3 mb-6">
    <!-- Bootcamp count -->
    <div>
      <span class="text-3xl font-bold text-text-primary">{{ activeCount }}</span>
      <span class="text-text-secondary ml-2 text-sm">bootcamps scheduled</span>
    </div>

    <div class="flex items-center gap-3">
      <!-- Greedy / Optimal toggle -->
      <div class="flex rounded-xl overflow-hidden border border-border text-sm">
        <button
          v-for="s in solvers"
          :key="s.key"
          @click="emit('update:active', s.key)"
          :class="[
            'px-3 py-1.5 font-medium transition-all duration-150',
            active === s.key
              ? 'bg-accent text-white'
              : 'bg-surface text-text-secondary hover:text-text-primary',
          ]"
        >
          {{ s.label }} ({{ s.count }})
        </button>
      </div>

      <!-- Table / Calendar toggle -->
      <div class="flex rounded-xl overflow-hidden border border-border text-sm">
        <button
          v-for="v in views"
          :key="v"
          @click="emit('update:view', v)"
          :class="[
            'px-3 py-1.5 font-medium transition-all duration-150 capitalize',
            view === v
              ? 'bg-accent text-white'
              : 'bg-surface text-text-secondary hover:text-text-primary',
          ]"
        >
          {{ v }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  results: Object,
  active: String,
  view: String,
})
const emit = defineEmits(['update:active', 'update:view'])

const solvers = computed(() => [
  { key: 'greedy', label: 'Greedy', count: props.results?.greedy?.total_bootcamps ?? 0 },
  { key: 'optimal', label: 'Optimal', count: props.results?.optimal?.total_bootcamps ?? 0 },
])

const views = ['table', 'calendar']

const activeCount = computed(
  () => props.results?.[props.active]?.total_bootcamps ?? 0
)
</script>
