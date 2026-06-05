import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Artwork } from '@/types'
import { getArtworks, getArtworkDetail, likeArtwork, favoriteArtwork, checkFavorite } from '@/api'

export const useArtworkStore = defineStore('artwork', () => {
  const artworks = ref<Artwork[]>([])
  const currentArtwork = ref<Artwork | null>(null)
  const loading = ref(false)
  const favorited = ref(false)
  const favoriteId = ref<number | null>(null)

  async function fetchArtworks(params?: Record<string, string>) {
    loading.value = true
    try {
      artworks.value = await getArtworks(params)
    } finally {
      loading.value = false
    }
  }

  async function fetchArtworkDetail(id: number) {
    loading.value = true
    try {
      currentArtwork.value = await getArtworkDetail(id)
      const status = await checkFavorite('artwork', id)
      favorited.value = status.favorited
      favoriteId.value = status.favorite_id
    } finally {
      loading.value = false
    }
  }

  async function doLike(id: number) {
    await likeArtwork(id)
    if (currentArtwork.value && currentArtwork.value.id === id) {
      currentArtwork.value.likes++
    }
  }

  async function doFavorite(id: number) {
    const result = await favoriteArtwork(id)
    favorited.value = result.favorited
    if (currentArtwork.value && currentArtwork.value.id === id) {
      currentArtwork.value.favorites = result.favorites
    }
    const artwork = artworks.value.find(a => a.id === id)
    if (artwork) {
      artwork.favorites = result.favorites
    }
    return result
  }

  return { artworks, currentArtwork, loading, favorited, favoriteId, fetchArtworks, fetchArtworkDetail, doLike, doFavorite }
})
