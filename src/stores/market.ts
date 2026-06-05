import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { KitListing, KitMatch } from '@/types'
import {
  getListings,
  createListing,
  getListingDetail,
  getListingMatches,
  updateListingStatus,
  favoriteListing,
  checkFavorite,
} from '@/api'

export const useMarketStore = defineStore('market', () => {
  const listings = ref<KitListing[]>([])
  const currentListing = ref<KitListing | null>(null)
  const matches = ref<KitMatch[]>([])
  const loading = ref(false)
  const favorited = ref(false)
  const favoriteId = ref<number | null>(null)

  async function fetchListings(params?: Record<string, string>) {
    loading.value = true
    try {
      listings.value = await getListings(params)
    } finally {
      loading.value = false
    }
  }

  async function fetchListingDetail(id: number) {
    loading.value = true
    try {
      currentListing.value = await getListingDetail(id)
      const status = await checkFavorite('listing', id)
      favorited.value = status.favorited
      favoriteId.value = status.favorite_id
    } finally {
      loading.value = false
    }
  }

  async function fetchMatches(id: number) {
    try {
      matches.value = await getListingMatches(id)
    } catch {
      matches.value = []
    }
  }

  async function publishListing(payload: Partial<KitListing>) {
    return createListing(payload)
  }

  async function patchStatus(id: number, status: string) {
    return updateListingStatus(id, status)
  }

  async function doFavorite(id: number) {
    const result = await favoriteListing(id)
    favorited.value = result.favorited
    if (currentListing.value && currentListing.value.id === id) {
      currentListing.value.favorites = result.favorites
    }
    const listing = listings.value.find(l => l.id === id)
    if (listing) {
      listing.favorites = result.favorites
    }
    return result
  }

  return { listings, currentListing, matches, loading, favorited, favoriteId, fetchListings, fetchListingDetail, fetchMatches, publishListing, patchStatus, doFavorite }
})
