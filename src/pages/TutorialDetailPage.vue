<template>
  <div>
    <div class="flex items-center gap-3 mb-6">
      <button class="kit-btn-secondary text-xs" @click="router.back()">
        <ArrowLeft :size="14" class="inline mr-1" />返回
      </button>
      <h2 class="section-title">教程详情</h2>
    </div>

    <div v-if="store.loading" class="text-center py-20 text-gray-500">加载中...</div>
    <template v-else-if="store.currentTutorial">
      <div class="kit-card p-6 mb-6">
        <div class="flex items-start justify-between mb-4">
          <div>
            <h3 class="font-display text-xl font-bold text-military-sand mb-2">{{ store.currentTutorial.title }}</h3>
            <div class="flex items-center gap-3 text-sm text-gray-500">
              <span class="flex items-center gap-1"><User :size="14" />达人#{{ store.currentTutorial.user_id }}</span>
              <span class="flex items-center gap-1"><Calendar :size="14" />{{ store.currentTutorial.created_at?.slice(0, 10) }}</span>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <span class="kit-tag-sand text-xs">{{ store.currentTutorial.subject }}</span>
            <span
              class="kit-tag text-xs"
              :class="{
                'bg-green-900/30 text-green-400 border-green-700/40': store.currentTutorial.difficulty === 'beginner',
                'bg-yellow-900/30 text-yellow-400 border-yellow-700/40': store.currentTutorial.difficulty === 'intermediate',
                'bg-red-900/30 text-red-400 border-red-700/40': store.currentTutorial.difficulty === 'advanced',
              }"
            >
              {{ difficultyLabel(store.currentTutorial.difficulty) }}
            </span>
          </div>
        </div>
        <div class="flex items-center gap-6 text-sm text-gray-400 mb-4">
          <span class="flex items-center gap-1"><Eye :size="14" />{{ store.currentTutorial.views }} 浏览</span>
          <span class="flex items-center gap-1"><CheckCircle :size="14" />{{ store.currentTutorial.completions }} 完成</span>
          <span class="flex items-center gap-1"><Heart :size="14" />{{ store.currentTutorial.favorites }} 收藏</span>
        </div>
        <div class="flex gap-3">
          <button class="kit-btn-primary flex items-center gap-2 text-xs" @click="handleFavorite">
            <Heart :size="14" />收藏
          </button>
          <button class="kit-btn-secondary flex items-center gap-2 text-xs" @click="handleComplete">
            <CheckCircle :size="14" />标记完成
          </button>
        </div>
      </div>

      <div v-if="store.currentTutorial.steps?.length > 0" class="kit-card p-6 mb-6">
        <h3 class="font-display font-semibold text-military-sand tracking-wide mb-6">制作步骤</h3>
        <div class="relative pl-8">
          <div class="absolute left-3 top-0 bottom-0 w-px bg-military-olive/30"></div>
          <div v-for="step in store.currentTutorial.steps" :key="step.order_num" class="relative mb-8 last:mb-0">
            <div class="absolute -left-5 w-6 h-6 rounded-full bg-military-olive flex items-center justify-center text-white text-xs font-display font-bold">
              {{ step.order_num }}
            </div>
            <div class="bg-military-bg rounded p-4">
              <h4 class="font-display font-semibold text-military-sand text-sm mb-2">{{ step.title }}</h4>
              <p class="text-sm text-gray-400 leading-relaxed mb-2">{{ step.description }}</p>
              <div v-if="step.technique" class="flex items-center gap-2 mt-2">
                <Zap :size="12" class="text-military-sand" />
                <span class="kit-tag-sand text-xs">{{ step.technique }}</span>
              </div>
              <div class="mt-3 h-32 bg-military-bg-light rounded flex items-center justify-center">
                <ImageIcon :size="24" class="text-military-olive/20" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="store.currentTutorial.paints?.length > 0" class="kit-card p-6 mb-6">
        <h3 class="font-display font-semibold text-military-sand tracking-wide mb-4">使用颜料</h3>
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          <div
            v-for="(paint, i) in store.currentTutorial.paints"
            :key="i"
            class="bg-military-bg rounded p-3"
          >
            <div class="w-full h-10 rounded mb-2" :style="{ backgroundColor: paint.color_code || '#555' }"></div>
            <div class="text-sm text-gray-200 font-medium">{{ paint.name }}</div>
            <div class="text-xs text-gray-500">{{ paint.brand }} · {{ paint.color_code }}</div>
            <div class="text-xs text-gray-400 mt-1">{{ paint.usage }}</div>
          </div>
        </div>
      </div>

      <div v-if="store.currentTutorial.weathering_details?.length > 0" class="kit-card p-6">
        <h3 class="font-display font-semibold text-military-sand tracking-wide mb-4">旧化技法</h3>
        <div class="space-y-3">
          <div
            v-for="(w, i) in store.currentTutorial.weathering_details"
            :key="i"
            class="bg-military-bg rounded"
          >
            <button
              class="w-full flex items-center justify-between p-4 text-left"
              @click="toggleWeathering(i)"
            >
              <div class="flex items-center gap-2">
                <Flame :size="14" class="text-military-rust-light" />
                <span class="font-display font-semibold text-military-sand text-sm">{{ w.type }}</span>
              </div>
              <ChevronDown :size="16" class="text-gray-500 transition-transform" :class="{ 'rotate-180': expandedWeathering === i }" />
            </button>
            <div v-if="expandedWeathering === i" class="px-4 pb-4 space-y-2">
              <div class="text-xs text-gray-500">
                <span class="text-gray-400">产品:</span> {{ w.products.join('、') }}
              </div>
              <div class="text-xs text-gray-500">
                <span class="text-gray-400">技法:</span> {{ w.technique }}
              </div>
              <div class="text-xs text-gray-500">
                <span class="text-gray-400">说明:</span> {{ w.description }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, User, Calendar, Eye, CheckCircle, Heart, Zap, Flame, ChevronDown, Image as ImageIcon } from 'lucide-vue-next'
import { useTutorialStore } from '@/stores/tutorial'

const route = useRoute()
const router = useRouter()
const store = useTutorialStore()
const id = Number(route.params.id)
const expandedWeathering = ref<number | null>(null)

function difficultyLabel(d: string) {
  const map: Record<string, string> = { beginner: '入门', intermediate: '进阶', advanced: '大师' }
  return map[d] || d
}

function toggleWeathering(i: number) {
  expandedWeathering.value = expandedWeathering.value === i ? null : i
}

async function handleFavorite() {
  await store.doFavorite(id)
}

async function handleComplete() {
  await store.doComplete(id)
}

onMounted(() => {
  store.fetchTutorialDetail(id)
})
</script>
