<template>
  <div>
    <div class="flex items-center gap-3 mb-6">
      <h2 class="section-title">我的收藏</h2>
    </div>

    <div class="kit-card p-4 mb-6">
      <div class="flex flex-wrap items-center gap-2">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          class="kit-btn text-xs"
          :class="store.activeTab === tab.value ? 'kit-btn-primary' : 'kit-btn-secondary'"
          @click="switchTab(tab.value)"
        >
          <component :is="tab.icon" :size="14" class="inline mr-1" />
          {{ tab.label }}
        </button>
      </div>
    </div>

    <div v-if="store.loading" class="text-center py-20 text-gray-500">
      <Loader :size="24" class="inline animate-spin mr-2" />
      加载中...
    </div>
    <div v-else-if="store.error" class="text-center py-20">
      <div class="text-military-rust mb-2">
        <AlertCircle :size="32" class="mx-auto" />
      </div>
      <div class="text-gray-500 mb-4">{{ store.error }}</div>
      <button class="kit-btn-primary text-xs" @click="reload">重新加载</button>
    </div>
    <div v-else-if="store.filteredFavorites.length === 0" class="text-center py-20 text-gray-500">
      <Heart :size="48" class="mx-auto mb-3 text-gray-600" />
      <div class="font-display text-lg mb-1">暂无收藏</div>
      <div class="text-sm">快去浏览并收藏你感兴趣的内容吧</div>
    </div>
    <div v-else>
      <div v-if="store.activeTab === 'all' || store.activeTab === 'listing'" class="mb-8">
        <h3 v-if="store.activeTab === 'all' && store.listingFavorites.length > 0" class="font-display font-semibold text-military-sand mb-4 flex items-center gap-2">
          <ShoppingCart :size="16" />
          板件 ({{ store.listingFavorites.length }})
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="item in store.listingFavorites"
            :key="item.id"
            class="kit-card group"
          >
            <div class="p-4 cursor-pointer" @click="goListingDetail(item.target_id)">
              <div class="flex items-center justify-between mb-2">
                <span class="military-id">KIT-{{ String(item.target_id).padStart(3, '0') }}</span>
                <span
                  class="kit-tag text-xs"
                  :class="item.target.type === 'sell' ? 'kit-tag-olive' : 'kit-tag-rust'"
                >
                  {{ item.target.type === 'sell' ? '出售' : '求购' }}
                </span>
              </div>
              <h4 class="font-display font-semibold text-military-sand text-base mb-2 line-clamp-1">{{ item.target.title }}</h4>
              <div class="flex flex-wrap gap-1 mb-3">
                <span class="kit-tag-steel text-xs">{{ item.target.scale }}</span>
                <span class="kit-tag-sand text-xs">{{ item.target.manufacturer }}</span>
                <span class="kit-tag-olive text-xs">{{ conditionLabel(item.target.condition) }}</span>
              </div>
              <div class="flex items-center justify-between mt-3 pt-3 border-t border-military-olive/10">
                <span class="font-display text-lg font-bold text-military-sand">¥{{ item.target.price }}</span>
                <div class="flex items-center gap-2 text-xs text-gray-500">
                  <User :size="12" />
                  <span>玩家#{{ item.target.user_id }}</span>
                </div>
              </div>
            </div>
            <div class="px-4 pb-4 flex justify-end">
              <button class="kit-btn-secondary text-xs flex items-center gap-1 group-hover:bg-military-rust/20 transition-colors" @click="removeFavorite(item.id, 'listing', item.target_id)">
                <Trash2 :size="12" />
                取消收藏
              </button>
            </div>
          </div>
        </div>
      </div>

      <div v-if="store.activeTab === 'all' || store.activeTab === 'tutorial'" class="mb-8">
        <h3 v-if="store.activeTab === 'all' && store.tutorialFavorites.length > 0" class="font-display font-semibold text-military-sand mb-4 flex items-center gap-2">
          <BookOpen :size="16" />
          教程 ({{ store.tutorialFavorites.length }})
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="item in store.tutorialFavorites"
            :key="item.id"
            class="kit-card group"
          >
            <div class="cursor-pointer" @click="goTutorialDetail(item.target_id)">
              <div class="h-40 bg-military-bg-light flex items-center justify-center">
                <BookOpen :size="40" class="text-military-olive/30" />
              </div>
              <div class="p-4">
                <div class="flex items-center gap-2 mb-2">
                  <span class="kit-tag-sand text-xs">{{ item.target.subject }}</span>
                  <span
                    class="kit-tag text-xs"
                    :class="{
                      'bg-green-900/30 text-green-400 border-green-700/40': item.target.difficulty === 'beginner',
                      'bg-yellow-900/30 text-yellow-400 border-yellow-700/40': item.target.difficulty === 'intermediate',
                      'bg-red-900/30 text-red-400 border-red-700/40': item.target.difficulty === 'advanced',
                    }"
                  >
                    {{ difficultyLabel(item.target.difficulty) }}
                  </span>
                </div>
                <h4 class="font-display font-semibold text-military-sand text-base mb-3 line-clamp-1">{{ item.target.title }}</h4>
                <div class="flex items-center gap-4 text-xs text-gray-500">
                  <span class="flex items-center gap-1"><Eye :size="12" />{{ item.target.views }}</span>
                  <span class="flex items-center gap-1"><CheckCircle :size="12" />{{ item.target.completions }}</span>
                  <span class="flex items-center gap-1"><Heart :size="12" />{{ item.target.favorites }}</span>
                </div>
              </div>
            </div>
            <div class="px-4 pb-4 flex justify-end">
              <button class="kit-btn-secondary text-xs flex items-center gap-1 group-hover:bg-military-rust/20 transition-colors" @click="removeFavorite(item.id, 'tutorial', item.target_id)">
                <Trash2 :size="12" />
                取消收藏
              </button>
            </div>
          </div>
        </div>
      </div>

      <div v-if="store.activeTab === 'all' || store.activeTab === 'artwork'" class="mb-8">
        <h3 v-if="store.activeTab === 'all' && store.artworkFavorites.length > 0" class="font-display font-semibold text-military-sand mb-4 flex items-center gap-2">
          <ImageIcon :size="16" />
          作品 ({{ store.artworkFavorites.length }})
        </h3>
        <div class="columns-1 md:columns-2 lg:columns-3 gap-4 space-y-4">
          <div
            v-for="item in store.artworkFavorites"
            :key="item.id"
            class="kit-card break-inside-avoid group"
          >
            <div class="cursor-pointer" @click="goArtworkDetail(item.target_id)">
              <div
                class="bg-military-bg-light flex items-center justify-center"
                :style="{ height: heights[item.id % heights.length] + 'px' }"
              >
                <ImageIcon :size="36" class="text-military-olive/20" />
              </div>
              <div class="p-3">
                <h4 class="font-display font-semibold text-military-sand text-sm mb-1 line-clamp-1">{{ item.target.title }}</h4>
                <div class="flex flex-wrap gap-1 mb-2">
                  <span v-for="tech in item.target.techniques.slice(0, 3)" :key="tech" class="kit-tag-olive text-xs">{{ tech }}</span>
                </div>
                <div class="flex items-center gap-3 text-xs text-gray-500">
                  <span class="flex items-center gap-1"><ThumbsUp :size="12" />{{ item.target.likes }}</span>
                  <span class="flex items-center gap-1"><Heart :size="12" />{{ item.target.favorites }}</span>
                </div>
              </div>
            </div>
            <div class="px-3 pb-3 flex justify-end">
              <button class="kit-btn-secondary text-xs flex items-center gap-1 group-hover:bg-military-rust/20 transition-colors" @click="removeFavorite(item.id, 'artwork', item.target_id)">
                <Trash2 :size="12" />
                取消收藏
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Heart, ShoppingCart, BookOpen, Image as ImageIcon, Trash2, Loader, AlertCircle, User, Eye, CheckCircle, ThumbsUp } from 'lucide-vue-next'
import { useFavoriteStore } from '@/stores/favorite'
import { useFavorite } from '@/composables/useFavorite'
import { useMarketStore } from '@/stores/market'
import { useTutorialStore } from '@/stores/tutorial'
import { useArtworkStore } from '@/stores/artwork'
import type { FavoriteTargetType } from '@/types'

const store = useFavoriteStore()
const router = useRouter()
const marketStore = useMarketStore()
const tutorialStore = useTutorialStore()
const artworkStore = useArtworkStore()

const { doUnfavorite } = useFavorite({
  targetType: 'listing',
  onUpdateFavorites: (id, count) => {
    marketStore.updateListingFavorites(id, count)
    tutorialStore.updateTutorialFavorites(id, count)
    artworkStore.updateArtworkFavorites(id, count)
  },
})

const tabs = [
  { label: '全部', value: 'all' as const, icon: Heart },
  { label: '板件', value: 'listing' as const, icon: ShoppingCart },
  { label: '教程', value: 'tutorial' as const, icon: BookOpen },
  { label: '作品', value: 'artwork' as const, icon: ImageIcon },
]

const heights = [200, 260, 180, 240, 220, 280]

function conditionLabel(c: string) {
  const map: Record<string, string> = { sealed: '全新未拆', opened: '已拆封', partial: '部分零件', damaged: '有损伤' }
  return map[c] || c
}

function difficultyLabel(d: string) {
  const map: Record<string, string> = { beginner: '入门', intermediate: '进阶', advanced: '大师' }
  return map[d] || d
}

function switchTab(tab: FavoriteTargetType | 'all') {
  store.setActiveTab(tab)
}

function goListingDetail(id: number) {
  router.push(`/market/detail/${id}`)
}

function goTutorialDetail(id: number) {
  router.push(`/tutorials/${id}`)
}

function goArtworkDetail(id: number) {
  router.push(`/gallery/${id}`)
}

async function removeFavorite(favoriteId: number, targetType: FavoriteTargetType, targetId: number) {
  const success = await doUnfavorite(favoriteId, targetId)
  if (success) {
    if (targetType === 'listing') {
      marketStore.updateListingFavorites(targetId, Math.max(0, (marketStore.listings.find(l => l.id === targetId)?.favorites ?? 1) - 1))
    } else if (targetType === 'tutorial') {
      tutorialStore.updateTutorialFavorites(targetId, Math.max(0, (tutorialStore.tutorials.find(t => t.id === targetId)?.favorites ?? 1) - 1))
    } else if (targetType === 'artwork') {
      artworkStore.updateArtworkFavorites(targetId, Math.max(0, (artworkStore.artworks.find(a => a.id === targetId)?.favorites ?? 1) - 1))
    }
  }
}

function reload() {
  store.fetchFavorites()
}

onMounted(() => {
  store.fetchFavorites()
})
</script>
