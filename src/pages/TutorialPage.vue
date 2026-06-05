<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h2 class="section-title">技法教程</h2>
      <router-link to="/tutorials/publish" class="kit-btn-primary flex items-center gap-2">
        <Plus :size="16" />
        发布教程
      </router-link>
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
        <span class="text-xs text-gray-400 font-display">难度</span>
        <button
          v-for="d in difficultyOptions"
          :key="d.value"
          class="kit-btn text-xs"
          :class="filters.difficulty === d.value ? 'kit-btn-primary' : 'kit-btn-secondary'"
          @click="filters.difficulty = d.value; applyFilters()"
        >
          {{ d.label }}
        </button>
      </div>
    </div>

    <div v-if="store.loading" class="text-center py-20 text-gray-500">加载中...</div>
    <div v-else-if="store.tutorials.length === 0" class="text-center py-20 text-gray-500">暂无教程</div>
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="tutorial in store.tutorials"
        :key="tutorial.id"
        class="kit-card cursor-pointer"
        @click="goDetail(tutorial.id)"
      >
        <div class="h-40 bg-military-bg-light flex items-center justify-center">
          <BookOpen :size="40" class="text-military-olive/30" />
        </div>
        <div class="p-4">
          <div class="flex items-center gap-2 mb-2">
            <span class="kit-tag-sand text-xs">{{ tutorial.subject }}</span>
            <span
              class="kit-tag text-xs"
              :class="{
                'bg-green-900/30 text-green-400 border-green-700/40': tutorial.difficulty === 'beginner',
                'bg-yellow-900/30 text-yellow-400 border-yellow-700/40': tutorial.difficulty === 'intermediate',
                'bg-red-900/30 text-red-400 border-red-700/40': tutorial.difficulty === 'advanced',
              }"
            >
              {{ difficultyLabel(tutorial.difficulty) }}
            </span>
          </div>
          <h3 class="font-display font-semibold text-military-sand text-base mb-3 line-clamp-1">{{ tutorial.title }}</h3>
          <div class="flex items-center gap-4 text-xs text-gray-500">
            <span class="flex items-center gap-1"><Eye :size="12" />{{ tutorial.views }}</span>
            <span class="flex items-center gap-1"><CheckCircle :size="12" />{{ tutorial.completions }}</span>
            <span class="flex items-center gap-1"><Heart :size="12" />{{ tutorial.favorites }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, BookOpen, Eye, CheckCircle, Heart } from 'lucide-vue-next'
import { useTutorialStore } from '@/stores/tutorial'

const store = useTutorialStore()
const router = useRouter()

const subjectOptions = ['全部', '坦克', '战斗机', '战舰', '通用技巧']
const difficultyOptions = [
  { label: '全部', value: '' },
  { label: '入门', value: 'beginner' },
  { label: '进阶', value: 'intermediate' },
  { label: '大师', value: 'advanced' },
]

const filters = reactive({
  subject: '全部',
  difficulty: '',
})

function difficultyLabel(d: string) {
  const map: Record<string, string> = { beginner: '入门', intermediate: '进阶', advanced: '大师' }
  return map[d] || d
}

function applyFilters() {
  const params: Record<string, string> = {}
  if (filters.subject && filters.subject !== '全部') params.subject = filters.subject
  if (filters.difficulty) params.difficulty = filters.difficulty
  store.fetchTutorials(params)
}

function goDetail(id: number) {
  router.push(`/tutorials/${id}`)
}

onMounted(() => {
  store.fetchTutorials()
})
</script>
