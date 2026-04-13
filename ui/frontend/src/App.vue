<template>
  <div class="min-h-screen bg-bg text-text-primary font-sans">
    <!-- Header -->
    <header class="border-b border-border px-6 py-4 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <span class="text-xl font-bold tracking-tight">Bootcamp Scheduler</span>
      </div>
    </header>

    <!-- Error Toast -->
    <Transition name="toast">
      <div
        v-if="error"
        class="fixed top-4 right-4 z-50 bg-surface border border-red-500/50 rounded-xl px-4 py-3
               shadow-xl max-w-sm flex items-start gap-3"
      >
        <svg class="w-4 h-4 text-red-400 mt-0.5 shrink-0" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
        </svg>
        <div class="flex-1 min-w-0">
          <p class="text-red-400 text-sm font-medium">Error</p>
          <p class="text-text-secondary text-xs mt-0.5">{{ error }}</p>
        </div>
        <button @click="dismissError" class="text-text-secondary hover:text-text-primary">
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
          </svg>
        </button>
      </div>
    </Transition>

    <!-- Main layout -->
    <main class="flex gap-6 p-6 max-w-[1400px] mx-auto items-start">
      <!-- Control Panel -->
      <ControlPanel
        :files="files"
        :trainers="trainers"
        :trainer-categories="trainerCategories"
        :selected-file="selectedFile"
        :solver="solver"
        :apply-bank-holidays="applyBankHolidays"
        :loading="loading"
        :elapsed-seconds="elapsedSeconds"
        @run="runSchedule"
        @update:selectedFile="selectedFile = $event"
        @update:solver="solver = $event"
        @update:applyBankHolidays="applyBankHolidays = $event"
        @fileChange="fetchTrainers"
      />

      <!-- Results Area -->
      <div class="flex-1 min-w-0">
        <!-- Loading -->
        <LoadingSpinner v-if="loading" :solver="solver" :elapsed="elapsedSeconds" />

        <!-- Empty state (no run yet) -->
        <div
          v-else-if="!hasResults"
          class="flex flex-col items-center justify-center py-24 text-text-secondary"
        >
          <svg class="w-12 h-12 mb-4 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                  d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
          </svg>
          <p class="font-medium">No schedule yet</p>
          <p class="text-sm mt-1">Configure options and click Generate Schedule</p>
        </div>

        <!-- Results -->
        <div v-else>
          <ResultsHeader
            :results="results"
            :active="activeResult"
            :view="view"
            @update:active="activeResult = $event"
            @update:view="view = $event"
          />

          <div class="bg-surface border border-border rounded-xl p-6">
            <ScheduleTable
              v-if="view === 'table'"
              :schedule="currentSchedule"
              :trainer-categories="trainerCategories"
            />
            <ScheduleCalendar
              v-else
              :schedule="currentSchedule"
            />
          </div>

          <!-- Export row -->
          <div class="flex gap-3 mt-4">
            <button
              @click="exportCSV"
              class="px-4 py-2 rounded-lg border border-border text-text-secondary text-sm
                     hover:border-accent/50 hover:text-accent transition-all duration-150"
            >
              Export CSV
            </button>
            <button
              @click="exportJSON"
              class="px-4 py-2 rounded-lg border border-border text-text-secondary text-sm
                     hover:border-accent/50 hover:text-accent transition-all duration-150"
            >
              Export JSON
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useScheduler } from './composables/useScheduler.js'
import ControlPanel from './components/ControlPanel.vue'
import ResultsHeader from './components/ResultsHeader.vue'
import ScheduleTable from './components/ScheduleTable.vue'
import ScheduleCalendar from './components/ScheduleCalendar.vue'
import LoadingSpinner from './components/LoadingSpinner.vue'

const {
  files,
  trainers,
  trainerCategories,
  selectedFile,
  solver,
  applyBankHolidays,
  loading,
  elapsedSeconds,
  error,
  results,
  activeResult,
  hasResults,
  fetchFiles,
  fetchTrainers,
  runSchedule,
  dismissError,
} = useScheduler()

const view = ref('table')

const currentSchedule = computed(
  () => results[activeResult.value]?.schedule ?? []
)

onMounted(async () => {
  await fetchFiles()
})

// Auto-dismiss error after 5s
import { watch } from 'vue'
watch(error, (val) => {
  if (val) setTimeout(dismissError, 5000)
})

function exportCSV() {
  const rows = [['date1', 'date2', 'trainers', 'location']]
  for (const entry of currentSchedule.value) {
    const [d1, d2] = entry.slot
    rows.push([d1, d2, entry.trainers.join('; '), entry.location ?? ''])
  }
  const csv = rows.map((r) => r.join(',')).join('\n')
  download('schedule.csv', csv, 'text/csv')
}

function exportJSON() {
  download('schedule.json', JSON.stringify(currentSchedule.value, null, 2), 'application/json')
}

function download(filename, content, type) {
  const blob = new Blob([content], { type })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<style>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.2s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(1rem);
}
</style>
