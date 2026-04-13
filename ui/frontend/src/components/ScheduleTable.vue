<template>
  <div>
    <div v-if="!schedule || schedule.length === 0" class="text-center py-16 text-text-secondary">
      No bootcamps could be scheduled with the current constraints.
    </div>

    <table v-else class="w-full text-sm">
      <thead>
        <tr class="border-b border-border text-text-secondary text-left">
          <th class="pb-3 pr-6 font-medium">Slot</th>
          <th class="pb-3 pr-6 font-medium">Trainers</th>
          <th class="pb-3 font-medium">Location</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(entry, i) in schedule"
          :key="i"
          class="border-b border-border/50 transition-all duration-150 hover:bg-surface/50"
          :style="{ animationDelay: `${i * 50}ms` }"
        >
          <td class="py-3 pr-6 font-mono text-xs text-text-primary whitespace-nowrap">
            {{ formatSlot(entry.slot) }}
          </td>
          <td class="py-3 pr-6">
            <div class="flex flex-wrap gap-1">
              <span
                v-for="trainer in entry.trainers"
                :key="trainer"
                :class="['px-2 py-0.5 rounded-lg text-xs font-medium', trainerBadgeClass(trainer)]"
              >
                {{ trainer }}
              </span>
            </div>
          </td>
          <td class="py-3 text-text-primary">
            {{ locationDisplay(entry.location) }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
const props = defineProps({
  schedule: Array,
  trainerCategories: Object,
})

const LOCATION_FLAGS = {
  london: '🇬🇧',
  manchester: '🇬🇧',
  bristol: '🇬🇧',
  paris: '🇫🇷',
  amsterdam: '🇳🇱',
  stockholm: '🇸🇪',
}

function formatSlot(slot) {
  const [d1, d2] = slot
  const fmt = (s) => {
    const d = new Date(s + 'T00:00:00')
    return d.toLocaleDateString('en-GB', {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
    })
  }
  const year = new Date(d2 + 'T00:00:00').getFullYear()
  return `${fmt(d1)} – ${fmt(d2)} ${year}`
}

function trainerBadgeClass(name) {
  const cat = props.trainerCategories?.[name] ?? 'uncategorised'
  if (cat === 'experienced') return 'bg-accent/20 text-accent border border-accent/30'
  if (cat === 'trainee') return 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
  return 'bg-[#2a2a2a] text-text-secondary border border-border'
}

function locationDisplay(location) {
  if (!location) return '—'
  const flag = LOCATION_FLAGS[location.toLowerCase()] ?? ''
  return `${flag} ${location}`
}
</script>
