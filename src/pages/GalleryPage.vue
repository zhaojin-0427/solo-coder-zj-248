<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h2 class="section-title">作品展示</h2>
    </div>

    <div class="kit-card p-4 mb-6">
      <div class="flex flex-wrap items-center gap-3 mb-3">
        <span class="text-xs text-gray-400 font-display">题材</span>
        <button
          v-for="s in subjectOptions"
          :key="s"
          class="kit-btn text-xs"
          :class="filters.subject === s ? 'kit-btn-primary' : 'kit-btn-secondary'"
          @click="filters.subject = s; applyFilters()"
        >
          {{ s }}
        </button>
      </div>
      <div class="flex flex-wrap items-center gap-3">
        <span class="text-xs text-gray-400 font-display">技法</span>
        <button
          v-for="t in techniqueOptions"
          :key="t"
          class="kit-btn text-xs"
          :class="filters.technique === t ? 'kit-btn-primary' : 'kit-btn-secondary'"
          @click="filters.technique = t; applyFilters()"
        >
          {{ t }}
        </button>
      </div>
    </div>

    <div v-if="store.loading" class="text-center py-20 text-gray-500">加载中...</div>
    <div v-else-if="store.artworks.length === 0" class="text-center py-20 text-gray-500">暂无作品</div>
    <div v-else class="columns-1 md:columns-2 lg:columns-3 gap-4 space-y-4">
      <div
        v-for="artwork in store.artworks"
        :key="artwork.id"
        class="kit-card break-inside-avoid cursor-pointer group"
        @click="goDetail(artwork.id)"
      >
        <div
          class="bg-military-bg-light flex items-center justify-center"
          :style="{ height: heights[artwork.id % heights.length] + 'px' }"
        >
          <ImageIcon :size="36" class="text-military-olive/20" />
        </div>
        <div class="p-3 relative">
          <h3 class="font-display font-semibold text-military-sand text-sm mb-1 line-clamp-1">{{ artwork.title }}</h3>
          <div class="flex flex-wrap gap-1 mb-2">
            <span v-for="tech in artwork.techniques.slice(0, 3)" :key="tech" class="kit-tag-olive text-xs">{{ tech }}</span>
          </div>
          <div class="flex items-center gap-3 text-xs text-gray-500">
            <span class="flex items-center gap-1"><ThumbsUp :size="12" />{{ artwork.likes }}</span>
            <span class="flex items-center gap-1"><Heart :size="12" />{{ artwork.favorites }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { Image as ImageIcon, ThumbsUp, Heart } from 'lucide-vue-next'
import { useArtworkStore } from '@/stores/artwork'

const store = useArtworkStore()
const router = useRouter()

const heights = [200, 260, 180, 300, 220, 280]

const subjectOptions = ['全部', '坦克', '战斗机', '战舰']
const techniqueOptions = ['全部', '干扫', '渍洗', '滤镜', '掉漆', '流锈', '泥浆', '喷涂渐变']

const filters = reactive({
  subject: '全部',
  technique: '全部',
})

function applyFilters() {
  const params: Record<string, string> = {}
  if (filters.subject && filters.subject !== '全部') params.subject = filters.subject
  if (filters.technique && filters.technique !== '全部') params.technique = filters.technique
  store.fetchArtworks(params)
}

function goDetail(id: number) {
  router.push(`/gallery/${id}`)
}

onMounted(() => {
  store.fetchArtworks()
})
</script>
