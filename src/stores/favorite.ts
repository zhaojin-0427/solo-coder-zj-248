import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { FavoriteWithTarget, FavoriteTargetType, KitListing, Tutorial, Artwork } from '@/types'
import { getFavorites, removeFavorite } from '@/api'

export const useFavoriteStore = defineStore('favorite', () => {
  const favorites = ref<FavoriteWithTarget[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const activeTab = ref<FavoriteTargetType | 'all'>('all')

  const listingFavorites = computed(() =>
    favorites.value.filter(f => f.target_type === 'listing') as (FavoriteWithTarget & { target: KitListing })[]
  )

  const tutorialFavorites = computed(() =>
    favorites.value.filter(f => f.target_type === 'tutorial') as (FavoriteWithTarget & { target: Tutorial })[]
  )

  const artworkFavorites = computed(() =>
    favorites.value.filter(f => f.target_type === 'artwork') as (FavoriteWithTarget & { target: Artwork })[]
  )

  const filteredFavorites = computed(() => {
    if (activeTab.value === 'all') return favorites.value
    if (activeTab.value === 'listing') return listingFavorites.value
    if (activeTab.value === 'tutorial') return tutorialFavorites.value
    if (activeTab.value === 'artwork') return artworkFavorites.value
    return []
  })

  async function fetchFavorites(targetType?: FavoriteTargetType) {
    loading.value = true
    error.value = null
    try {
      favorites.value = await getFavorites(targetType)
    } catch (e) {
      error.value = '加载收藏失败，请稍后重试'
      favorites.value = []
    } finally {
      loading.value = false
    }
  }

  async function deleteFavorite(favoriteId: number, targetType: FavoriteTargetType, targetId: number) {
    try {
      await removeFavorite(favoriteId)
      favorites.value = favorites.value.filter(f => f.id !== favoriteId)
      return true
    } catch (e) {
      error.value = '取消收藏失败，请稍后重试'
      return false
    }
  }

  function setActiveTab(tab: FavoriteTargetType | 'all') {
    activeTab.value = tab
  }

  function isFavorited(targetType: FavoriteTargetType, targetId: number): boolean {
    return favorites.value.some(f => f.target_type === targetType && f.target_id === targetId)
  }

  function getFavoriteId(targetType: FavoriteTargetType, targetId: number): number | null {
    const fav = favorites.value.find(f => f.target_type === targetType && f.target_id === targetId)
    return fav ? fav.id : null
  }

  return {
    favorites,
    loading,
    error,
    activeTab,
    listingFavorites,
    tutorialFavorites,
    artworkFavorites,
    filteredFavorites,
    fetchFavorites,
    deleteFavorite,
    setActiveTab,
    isFavorited,
    getFavoriteId,
  }
})
