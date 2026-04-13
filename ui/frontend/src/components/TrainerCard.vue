<template>
  <div class="flex items-center justify-between bg-surface border border-border rounded-xl px-4 py-3">
    <span class="text-text-primary text-sm font-medium truncate mr-3">{{ name }}</span>
    <div class="flex gap-1 shrink-0">
      <button
        v-for="option in options"
        :key="option.value"
        @click="select(option.value)"
        :class="[
          'px-2 py-1 rounded-lg text-xs font-semibold transition-all duration-150 border',
          category === option.value
            ? option.activeClass
            : 'bg-transparent border-border text-text-secondary hover:border-[#444]',
        ]"
      >
        {{ option.label }}
      </button>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  name: String,
  category: String,
})
const emit = defineEmits(['update:category'])

const options = [
  {
    value: 'experienced',
    label: 'Exp',
    activeClass: 'bg-accent border-accent text-white',
  },
  {
    value: 'uncategorised',
    label: 'Unc',
    activeClass: 'bg-[#2a2a2a] border-[#444] text-text-primary',
  },
  {
    value: 'trainee',
    label: 'New',
    activeClass: 'bg-amber-500 border-amber-500 text-white',
  },
]

function select(value) {
  emit('update:category', value)
}
</script>
