import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Tutorial } from '@/types'
import { getTutorials, createTutorial, getTutorialDetail, favoriteTutorial, completeTutorial, checkFavorite } from '@/api'

export const useTutorialStore = defineStore('tutorial', () => {
  const tutorials = ref<Tutorial[]>([])
  const currentTutorial = ref<Tutorial | null>(null)
  const loading = ref(false)
  const favorited = ref(false)
  const favoriteId = ref<number | null>(null)

  async function fetchTutorials(params?: Record<string, string>) {
    loading.value = true
    try {
      tutorials.value = await getTutorials(params)
    } finally {
      loading.value = false
    }
  }

  async function fetchTutorialDetail(id: number) {
    loading.value = true
    try {
      currentTutorial.value = await getTutorialDetail(id)
      const status = await checkFavorite('tutorial', id)
      favorited.value = status.favorited
      favoriteId.value = status.favorite_id
    } finally {
      loading.value = false
    }
  }

  async function publishTutorial(payload: Partial<Tutorial>) {
    return createTutorial(payload)
  }

  async function doFavorite(id: number) {
    const result = await favoriteTutorial(id)
    favorited.value = result.favorited
    if (currentTutorial.value && currentTutorial.value.id === id) {
      currentTutorial.value.favorites = result.favorites
    }
    const tutorial = tutorials.value.find(t => t.id === id)
    if (tutorial) {
      tutorial.favorites = result.favorites
    }
    return result
  }

  async function doComplete(id: number) {
    await completeTutorial(id)
    if (currentTutorial.value && currentTutorial.value.id === id) {
      currentTutorial.value.completions++
    }
  }

  return { tutorials, currentTutorial, loading, favorited, favoriteId, fetchTutorials, fetchTutorialDetail, publishTutorial, doFavorite, doComplete }
})
