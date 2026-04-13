<template>
  <div class="flex flex-col items-center justify-center gap-4 py-20">
    <div class="w-12 h-12 rounded-full border-4 border-border border-t-accent animate-spin"></div>
    <p class="text-text-secondary text-sm">
      Running {{ solverLabel }} solver<span class="font-mono ml-2 text-accent">{{ elapsed }}s</span>
    </p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  solver: String,
  elapsed: Number,
})

const solverLabel = computed(() =>
  props.solver === 'optimal' ? 'optimal' : 'greedy'
)
</script>
