<template>
  <div>
    <div class="flex items-center gap-3 mb-6">
      <button class="kit-btn-secondary text-xs" @click="router.back()">
        <ArrowLeft :size="14" class="inline mr-1" />返回
      </button>
      <h2 class="section-title">作品详情</h2>
    </div>

    <div v-if="store.loading" class="text-center py-20 text-gray-500">加载中...</div>
    <template v-else-if="store.currentArtwork">
      <div class="kit-card p-6 mb-6">
        <div class="h-80 bg-military-bg-light rounded flex items-center justify-center mb-4">
          <ImageIcon :size="64" class="text-military-olive/20" />
        </div>
        <div class="flex items-start justify-between mb-4">
          <div>
            <h3 class="font-display text-xl font-bold text-military-sand mb-2">{{ store.currentArtwork.title }}</h3>
            <div class="flex items-center gap-3 text-sm text-gray-500">
              <span class="flex items-center gap-1"><User :size="14" />玩家#{{ store.currentArtwork.user_id }}</span>
              <span class="flex items-center gap-1"><Calendar :size="14" />{{ store.currentArtwork.created_at?.slice(0, 10) }}</span>
            </div>
          </div>
          <div class="flex gap-2">
            <button class="kit-btn-secondary flex items-center gap-1 text-xs" @click="handleLike">
              <ThumbsUp :size="14" />{{ store.currentArtwork.likes }}
            </button>
            <button class="kit-btn-primary flex items-center gap-1 text-xs" @click="handleFavorite">
              <Heart :size="14" />{{ store.currentArtwork.favorites }}
            </button>
          </div>
        </div>
      </div>

      <div class="kit-card p-6 mb-6">
        <h3 class="font-display font-semibold text-military-sand tracking-wide mb-4">作品信息</h3>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="bg-military-bg rounded p-3">
            <div class="text-xs text-gray-500 font-display mb-1">板件名称</div>
            <div class="text-sm text-gray-200">{{ store.currentArtwork.kit_name }}</div>
          </div>
          <div class="bg-military-bg rounded p-3">
            <div class="text-xs text-gray-500 font-display mb-1">比例</div>
            <div class="text-sm text-gray-200">{{ store.currentArtwork.scale }}</div>
          </div>
          <div class="bg-military-bg rounded p-3">
            <div class="text-xs text-gray-500 font-display mb-1">题材</div>
            <div class="text-sm text-gray-200">{{ store.currentArtwork.subject }}</div>
          </div>
          <div class="bg-military-bg rounded p-3">
            <div class="text-xs text-gray-500 font-display mb-1">作者</div>
            <div class="text-sm text-gray-200">玩家#{{ store.currentArtwork.user_id }}</div>
          </div>
        </div>
      </div>

      <div v-if="store.currentArtwork.techniques.length > 0" class="kit-card p-6 mb-6">
        <h3 class="font-display font-semibold text-military-sand tracking-wide mb-4">使用技法</h3>
        <div class="flex flex-wrap gap-2">
          <span v-for="tech in store.currentArtwork.techniques" :key="tech" class="kit-tag-olive">{{ tech }}</span>
        </div>
      </div>

      <div v-if="store.currentArtwork.paints.length > 0" class="kit-card p-6 mb-6">
        <h3 class="font-display font-semibold text-military-sand tracking-wide mb-4">使用颜料</h3>
        <div class="flex flex-wrap gap-2">
          <span v-for="(paint, i) in store.currentArtwork.paints" :key="i" class="kit-tag-sand text-xs">{{ paint }}</span>
        </div>
      </div>

      <div v-if="store.currentArtwork.weathering.length > 0" class="kit-card p-6">
        <h3 class="font-display font-semibold text-military-sand tracking-wide mb-4">旧化技法</h3>
        <div class="flex flex-wrap gap-2">
          <span v-for="(w, i) in store.currentArtwork.weathering" :key="i" class="kit-tag-rust text-xs">{{ w }}</span>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, User, Calendar, ThumbsUp, Heart, Image as ImageIcon } from 'lucide-vue-next'
import { useArtworkStore } from '@/stores/artwork'

const route = useRoute()
const router = useRouter()
const store = useArtworkStore()
const id = Number(route.params.id)

async function handleLike() {
  await store.doLike(id)
}

async function handleFavorite() {
  await store.doFavorite(id)
}

onMounted(() => {
  store.fetchArtworkDetail(id)
})
</script>
