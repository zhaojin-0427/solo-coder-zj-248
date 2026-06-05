import { ref, computed } from 'vue'
import { useFavoriteStore } from '@/stores/favorite'
import type { FavoriteTargetType, FavoriteActionResponse, KitListing, Tutorial, Artwork } from '@/types'

interface UseFavoriteOptions<T> {
  targetType: FavoriteTargetType
  targetId?: number
  items?: T[]
  currentItem?: T | null
  onUpdateFavorites?: (id: number, count: number) => void
}

export function useFavorite<T extends { id: number; favorites: number }>(
  options: UseFavoriteOptions<T>
) {
  const favoriteStore = useFavoriteStore()
  const { targetType, targetId, items, currentItem, onUpdateFavorites } = options

  const localError = ref<string | null>(null)

  const favorited = computed(() => {
    if (targetId === undefined) return false
    return favoriteStore.isFavorited(targetType, targetId)
  })

  const favoriteId = computed(() => {
    if (targetId === undefined) return null
    return favoriteStore.getFavoriteId(targetType, targetId)
  })

  const actionLoading = computed(() => {
    if (targetId === undefined) return false
    return favoriteStore.isActionLoading(targetType, targetId)
  })

  function isItemFavorited(itemId: number): boolean {
    return favoriteStore.isFavorited(targetType, itemId)
  }

  function isItemActionLoading(itemId: number): boolean {
    return favoriteStore.isActionLoading(targetType, itemId)
  }

  function updateItemFavorites(itemId: number, count: number) {
    if (onUpdateFavorites) {
      onUpdateFavorites(itemId, count)
    } else {
      if (items) {
        const item = items.find(i => i.id === itemId)
        if (item) {
          item.favorites = count
        }
      }
      if (currentItem && currentItem.id === itemId) {
        currentItem.favorites = count
      }
    }
    favoriteStore.updateTargetFavorites(targetType, itemId, count)
  }

  async function doToggle(itemId?: number): Promise<FavoriteActionResponse | null> {
    const id = itemId ?? targetId
    if (id === undefined) {
      localError.value = '缺少目标ID'
      return null
    }

    const result = await favoriteStore.toggleFavorite(targetType, id)
    if (result) {
      updateItemFavorites(id, result.favorites)
    } else {
      localError.value = favoriteStore.error || '操作失败'
    }
    return result
  }

  async function doFavorite(itemId?: number): Promise<FavoriteActionResponse | null> {
    return doToggle(itemId)
  }

  async function doUnfavorite(favoriteId: number, itemId?: number, customTargetType?: FavoriteTargetType): Promise<boolean> {
    const id = itemId ?? targetId
    const actualTargetType = customTargetType ?? targetType
    if (id === undefined) {
      localError.value = '缺少目标ID'
      return false
    }

    const success = await favoriteStore.deleteFavorite(favoriteId, actualTargetType, id)
    if (success) {
      updateItemFavorites(id, Math.max(0, (items?.find(i => i.id === id)?.favorites ?? 1) - 1))
    } else {
      localError.value = favoriteStore.error || '取消收藏失败'
    }
    return success
  }

  async function checkAndSyncStatus(itemId: number): Promise<void> {
    if (!favoriteStore.isFavorited(targetType, itemId)) {
      const status = await favoriteStore.checkFavoriteStatus(targetType, itemId)
      if (status.favorited && status.favorite_id !== null) {
        const existing = favoriteStore.favorites.find(
          f => f.target_type === targetType && f.target_id === itemId
        )
        if (!existing) {
          const newFavorite = {
            id: status.favorite_id,
            user_id: 1,
            target_type: targetType,
            target_id: itemId,
            created_at: new Date().toISOString(),
            target: {} as any,
          }
          favoriteStore.favorites.unshift(newFavorite)
        }
      }
    }
  }

  function clearLocalError() {
    localError.value = null
  }

  return {
    favorited,
    favoriteId,
    actionLoading,
    localError,
    isItemFavorited,
    isItemActionLoading,
    doFavorite,
    doUnfavorite,
    doToggle,
    checkAndSyncStatus,
    updateItemFavorites,
    clearLocalError,
    favoriteStore,
  }
}

export function useListingFavorite() {
  return useFavorite<KitListing>({ targetType: 'listing' })
}

export function useTutorialFavorite() {
  return useFavorite<Tutorial>({ targetType: 'tutorial' })
}

export function useArtworkFavorite() {
  return useFavorite<Artwork>({ targetType: 'artwork' })
}
