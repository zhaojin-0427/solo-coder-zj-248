import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { SubjectStat, TurnoverStat, CompletionStat, FavoriteStat } from '@/types'
import { getPopularSubjects, getTurnoverSpeed, getTutorialCompletion, getTechniqueFavorites } from '@/api'

export const useStatisticsStore = defineStore('statistics', () => {
  const subjectStats = ref<SubjectStat[]>([])
  const turnoverStats = ref<TurnoverStat[]>([])
  const completionStats = ref<CompletionStat[]>([])
  const favoriteStats = ref<FavoriteStat[]>([])
  const loading = ref(false)

  async function fetchAll() {
    loading.value = true
    try {
      const [subjects, turnover, completion, favorites] = await Promise.all([
        getPopularSubjects(),
        getTurnoverSpeed(),
        getTutorialCompletion(),
        getTechniqueFavorites(),
      ])
      subjectStats.value = subjects
      turnoverStats.value = turnover
      completionStats.value = completion
      favoriteStats.value = favorites
    } finally {
      loading.value = false
    }
  }

  return { subjectStats, turnoverStats, completionStats, favoriteStats, loading, fetchAll }
})
