<template>
  <div>
    <div v-if="!schedule || schedule.length === 0" class="text-center py-16 text-text-secondary">
      No bootcamps could be scheduled with the current constraints.
    </div>

    <div v-else class="overflow-x-auto">
      <!-- Day header -->
      <div class="grid grid-cols-6 gap-1 mb-1">
        <div class="text-text-secondary text-xs text-right pr-2 py-1">Wk</div>
        <div
          v-for="day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']"
          :key="day"
          class="text-text-secondary text-xs text-center py-1 font-medium"
        >
          {{ day }}
        </div>
      </div>

      <!-- Weeks -->
      <div v-for="week in calendarWeeks" :key="week.isoWeek" class="grid grid-cols-6 gap-1 mb-1">
        <!-- Week label -->
        <div class="text-text-secondary text-xs text-right pr-2 pt-2 font-mono">
          W{{ week.isoWeek }}
        </div>

        <!-- Mon–Fri cells -->
        <template v-for="(cell, ci) in week.cells" :key="ci">
          <div
            v-if="cell.skip"
            class="hidden"
          ></div>
          <div
            v-else-if="cell.bootcamp"
            :class="[
              'rounded-lg px-2 py-2 text-xs font-medium bg-accent/80 text-white border border-accent/50',
              'hover:bg-accent cursor-default transition-colors duration-150 relative group',
              cell.colSpan === 2 ? 'col-span-2' : '',
            ]"
          >
            <div class="truncate">{{ cell.bootcamp.initials }}</div>
            <div v-if="cell.bootcamp.location" class="text-white/70 truncate text-[10px]">
              {{ cell.bootcamp.location }}
            </div>
            <!-- Tooltip -->
            <div
              class="absolute z-10 bottom-full left-0 mb-1 hidden group-hover:block
                     bg-[#111] border border-border rounded-xl p-3 min-w-[180px] shadow-xl"
            >
              <p class="font-semibold text-text-primary mb-1">{{ cell.bootcamp.dateRange }}</p>
              <p
                v-for="t in cell.bootcamp.trainers"
                :key="t"
                class="text-text-secondary text-[11px]"
              >
                {{ t }}
              </p>
              <p v-if="cell.bootcamp.location" class="text-accent text-[11px] mt-1">
                {{ cell.bootcamp.location }}
              </p>
            </div>
          </div>
          <div
            v-else
            class="rounded-lg bg-surface/50 border border-border/30 min-h-[52px]"
          ></div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  schedule: Array,
})

// Build a set of bootcamp events keyed by ISO date string
const bootcampByDate = computed(() => {
  const map = {}
  for (const entry of props.schedule ?? []) {
    const [d1, d2] = entry.slot
    const initials = entry.trainers.map((n) => n.split(' ').map((p) => p[0]).join('')).join(', ')
    const fmt = (s) => {
      const d = new Date(s + 'T00:00:00')
      return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })
    }
    const info = {
      dateRange: `${fmt(d1)} – ${fmt(d2)}`,
      trainers: entry.trainers,
      initials,
      location: entry.location ?? null,
      d2,
    }
    map[d1] = { ...info, isStart: true }
    map[d2] = { isEnd: true }
  }
  return map
})

// Determine the 4-week range from the schedule
const calendarWeeks = computed(() => {
  if (!props.schedule?.length) return []

  // Collect all dates
  const allDates = []
  for (const entry of props.schedule) {
    allDates.push(new Date(entry.slot[0] + 'T00:00:00'))
    allDates.push(new Date(entry.slot[1] + 'T00:00:00'))
  }
  allDates.sort((a, b) => a - b)

  // Start from Monday of the first date's week
  const firstDate = allDates[0]
  const startMonday = new Date(firstDate)
  const dow = startMonday.getDay() === 0 ? 6 : startMonday.getDay() - 1
  startMonday.setDate(startMonday.getDate() - dow)

  // Build weeks until we cover all dates + at least 4 weeks
  const lastDate = allDates[allDates.length - 1]
  const weeks = []
  const cursor = new Date(startMonday)

  while (cursor <= lastDate || weeks.length < 4) {
    const monday = new Date(cursor)
    const isoWeek = getISOWeek(monday)
    const cells = []

    for (let d = 0; d < 5; d++) {
      const day = new Date(monday)
      day.setDate(monday.getDate() + d)
      const isoStr = toISODateStr(day)
      const bc = bootcampByDate.value[isoStr]

      if (bc?.isStart) {
        cells.push({
          bootcamp: bc,
          colSpan: 2,
          skip: false,
        })
      } else if (bc?.isEnd) {
        cells.push({ skip: true })
      } else {
        cells.push({ skip: false })
      }
    }

    weeks.push({ isoWeek, cells })
    cursor.setDate(cursor.getDate() + 7)

    if (weeks.length >= 20) break // safety cap
  }

  return weeks
})

function toISODateStr(d) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function getISOWeek(d) {
  const date = new Date(d)
  date.setHours(0, 0, 0, 0)
  date.setDate(date.getDate() + 3 - ((date.getDay() + 6) % 7))
  const week1 = new Date(date.getFullYear(), 0, 4)
  return (
    1 +
    Math.round(
      ((date.getTime() - week1.getTime()) / 86400000 - 3 + ((week1.getDay() + 6) % 7)) / 7
    )
  )
}
</script>
