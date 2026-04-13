import { ref, reactive } from 'vue'
import axios from 'axios'

export function useScheduler() {
  const files = ref([])
  const trainers = ref([])
  const trainerCategories = reactive({})

  const selectedFile = ref('')
  const solver = ref('optimal')
  const applyBankHolidays = ref(true)

  const loading = ref(false)
  const elapsedSeconds = ref(0)
  const error = ref(null)

  const results = reactive({ greedy: null, optimal: null })
  const activeResult = ref('optimal')
  const hasResults = ref(false)

  let elapsedTimer = null

  async function fetchFiles() {
    const { data } = await axios.get('/api/files')
    files.value = data
    if (data.length > 0) {
      selectedFile.value = data[0]
      await fetchTrainers()
    }
  }

  async function fetchTrainers() {
    if (!selectedFile.value) return
    const { data } = await axios.get('/api/trainers', {
      params: { file: selectedFile.value },
    })
    trainers.value = data.trainers
    for (const name of data.trainers) {
      if (!(name in trainerCategories)) {
        trainerCategories[name] = 'uncategorised'
      }
    }
    // Remove old trainers that no longer exist in this file
    for (const name of Object.keys(trainerCategories)) {
      if (!data.trainers.includes(name)) {
        delete trainerCategories[name]
      }
    }
  }

  function buildConfig() {
    const experienced = []
    const trainees = []
    for (const [name, cat] of Object.entries(trainerCategories)) {
      if (cat === 'experienced') experienced.push(name)
      else if (cat === 'trainee') trainees.push(name)
    }
    return { experienced, trainees }
  }

  function startTimer() {
    elapsedSeconds.value = 0
    elapsedTimer = setInterval(() => {
      elapsedSeconds.value++
    }, 1000)
  }

  function stopTimer() {
    if (elapsedTimer) {
      clearInterval(elapsedTimer)
      elapsedTimer = null
    }
  }

  async function runSchedule() {
    loading.value = true
    error.value = null
    startTimer()

    try {
      const payload = {
        file: selectedFile.value,
        solver: solver.value,
        config: buildConfig(),
        apply_bank_holidays: applyBankHolidays.value,
      }

      const { data } = await axios.post('/api/schedule/compare', payload)
      results.greedy = data.greedy
      results.optimal = data.optimal
      activeResult.value = solver.value
      hasResults.value = true
    } catch (err) {
      error.value =
        err.response?.data?.detail || err.message || 'Unexpected error'
    } finally {
      loading.value = false
      stopTimer()
    }
  }

  function dismissError() {
    error.value = null
  }

  return {
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
  }
}
