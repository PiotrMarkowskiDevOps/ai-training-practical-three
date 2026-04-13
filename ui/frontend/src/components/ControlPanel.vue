<template>
  <aside class="w-80 shrink-0 flex flex-col gap-5">
    <!-- File Selector -->
    <section class="bg-surface border border-border rounded-xl p-4">
      <label class="block text-text-secondary text-xs font-semibold uppercase tracking-wider mb-2">
        Data Source
      </label>
      <select
        v-model="selectedFile"
        @change="onFileChange"
        class="w-full bg-bg border border-border rounded-lg px-3 py-2 text-text-primary text-sm
               focus:outline-none focus:ring-2 focus:ring-accent/40 transition-all duration-150"
      >
        <option v-for="f in files" :key="f" :value="f">{{ f }}</option>
      </select>
    </section>

    <!-- Trainer Categorisation -->
    <section v-if="trainers.length > 0" class="bg-surface border border-border rounded-xl p-4">
      <label class="block text-text-secondary text-xs font-semibold uppercase tracking-wider mb-3">
        Trainers
      </label>
      <div class="flex flex-col gap-2">
        <TrainerCard
          v-for="name in trainers"
          :key="name"
          :name="name"
          :category="trainerCategories[name]"
          @update:category="(v) => (trainerCategories[name] = v)"
        />
      </div>
    </section>

    <!-- Options -->
    <section class="bg-surface border border-border rounded-xl p-4">
      <label class="block text-text-secondary text-xs font-semibold uppercase tracking-wider mb-3">
        Options
      </label>
      <label class="flex items-center gap-3 cursor-pointer">
        <button
          @click="applyBankHolidays = !applyBankHolidays"
          :class="[
            'relative w-10 h-6 rounded-full transition-colors duration-150 shrink-0',
            applyBankHolidays ? 'bg-accent' : 'bg-border',
          ]"
        >
          <span
            :class="[
              'absolute top-1 w-4 h-4 bg-white rounded-full shadow transition-transform duration-150',
              applyBankHolidays ? 'translate-x-5' : 'translate-x-1',
            ]"
          ></span>
        </button>
        <div>
          <p class="text-text-primary text-sm font-medium">Apply Bank Holidays</p>
          <p class="text-text-secondary text-xs mt-0.5">
            Blocks trainers on public holidays for their home country
          </p>
        </div>
      </label>
    </section>

    <!-- Solver Toggle -->
    <section class="bg-surface border border-border rounded-xl p-4">
      <label class="block text-text-secondary text-xs font-semibold uppercase tracking-wider mb-3">
        Solver
      </label>
      <div class="flex gap-2">
        <button
          v-for="s in solverOptions"
          :key="s.value"
          @click="solver = s.value"
          :class="[
            'flex-1 py-2.5 rounded-xl font-semibold text-sm transition-all duration-150 border',
            solver === s.value
              ? 'bg-accent border-accent text-white'
              : 'bg-bg border-border text-text-secondary hover:text-text-primary hover:border-[#444]',
          ]"
          :title="s.tooltip"
        >
          {{ s.label }}
        </button>
      </div>
      <p v-if="solver === 'optimal'" class="text-text-secondary text-xs mt-2">
        Finds globally best solution — may take up to 30s
      </p>
    </section>

    <!-- Run Button -->
    <button
      @click="emit('run')"
      :disabled="loading || !selectedFile"
      class="w-full py-3 rounded-xl font-bold text-sm transition-all duration-150
             bg-accent text-white hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed
             focus:outline-none focus:ring-2 focus:ring-accent/40 flex items-center justify-center gap-2"
    >
      <svg
        v-if="loading"
        class="animate-spin w-4 h-4"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path
          class="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
        />
      </svg>
      <span v-if="loading">Running… {{ elapsedSeconds }}s</span>
      <span v-else>Generate Schedule</span>
    </button>
  </aside>
</template>

<script setup>
import TrainerCard from './TrainerCard.vue'

const props = defineProps({
  files: Array,
  trainers: Array,
  trainerCategories: Object,
  selectedFile: String,
  solver: String,
  applyBankHolidays: Boolean,
  loading: Boolean,
  elapsedSeconds: Number,
})

const emit = defineEmits(['run', 'update:selectedFile', 'update:solver', 'update:applyBankHolidays', 'fileChange'])

// v-model proxies via writable computed
import { computed } from 'vue'

const selectedFile = computed({
  get: () => props.selectedFile,
  set: (v) => emit('update:selectedFile', v),
})
const solver = computed({
  get: () => props.solver,
  set: (v) => emit('update:solver', v),
})
const applyBankHolidays = computed({
  get: () => props.applyBankHolidays,
  set: (v) => emit('update:applyBankHolidays', v),
})

function onFileChange() {
  emit('fileChange')
}

const solverOptions = [
  { value: 'greedy', label: 'Greedy', tooltip: 'Fast heuristic solver' },
  { value: 'optimal', label: 'Optimal', tooltip: 'Finds globally best solution — may take up to 30s' },
]
</script>
