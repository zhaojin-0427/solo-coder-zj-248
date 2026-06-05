<template>
  <div>
    <h2 class="section-title mb-6">工具推荐</h2>

    <div class="md:hidden kit-card p-3 mb-4">
      <div class="flex flex-wrap gap-1">
        <button
          v-for="cat in categories"
          :key="cat.value"
          class="kit-btn text-xs"
          :class="activeCategory === cat.value ? 'kit-btn-primary' : 'kit-btn-secondary'"
          @click="activeCategory = cat.value; applyFilter()"
        >
          {{ cat.label }}
        </button>
      </div>
    </div>

    <div class="flex flex-col md:flex-row gap-6">
      <div class="kit-card p-3 shrink-0 w-32 hidden md:block">
        <nav class="flex flex-col gap-1">
          <button
            v-for="cat in categories"
            :key="cat.value"
            class="text-left px-3 py-2 rounded text-xs font-display transition-colors"
            :class="activeCategory === cat.value ? 'bg-military-olive/20 text-military-sand' : 'text-gray-400 hover:text-military-sand hover:bg-military-bg-hover'"
            @click="activeCategory = cat.value; applyFilter()"
          >
            {{ cat.label }}
          </button>
        </nav>
      </div>

      <div class="flex-1">
        <div v-if="store.loading" class="text-center py-20 text-gray-500">加载中...</div>
        <div v-else-if="filteredTools.length === 0" class="text-center py-20 text-gray-500">暂无工具</div>
        <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div v-for="tool in filteredTools" :key="tool.id" class="kit-card p-4">
            <div class="flex gap-4">
              <div class="w-20 h-20 bg-military-bg-light rounded flex items-center justify-center shrink-0">
                <Wrench :size="24" class="text-military-olive/30" />
              </div>
              <div class="flex-1 min-w-0">
                <h3 class="font-display font-semibold text-military-sand text-sm mb-1">{{ tool.name }}</h3>
                <div class="text-xs text-gray-500 mb-2">{{ tool.brand }} · {{ categoryLabelMap[tool.category] || tool.category }}</div>
                <div class="flex items-center gap-1 mb-2">
                  <template v-for="n in 5" :key="n">
                    <Star
                      :size="12"
                      :class="n <= Math.round(tool.rating) ? 'text-military-sand fill-military-sand' : 'text-gray-600'"
                    />
                  </template>
                  <span class="text-xs text-gray-500 ml-1">{{ tool.rating.toFixed(1) }}</span>
                  <span class="text-xs text-gray-600">({{ tool.review_count }})</span>
                </div>
                <p class="text-xs text-gray-400 line-clamp-2 mb-2">{{ tool.description }}</p>
                <div v-if="tool.recommended_by.length > 0" class="flex items-center gap-1">
                  <div class="flex -space-x-1">
                    <div
                      v-for="(user, ui) in tool.recommended_by.slice(0, 3)"
                      :key="ui"
                      class="w-5 h-5 rounded-full bg-military-olive/30 border border-military-bg-card flex items-center justify-center text-xs text-military-sand font-display"
                    >
                      {{ user.charAt(0) }}
                    </div>
                  </div>
                  <span class="text-xs text-gray-500 ml-1">{{ tool.recommended_by.length }}人推荐</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { Wrench, Star } from 'lucide-vue-next'
import { useToolStore } from '@/stores/tool'

const store = useToolStore()
const activeCategory = ref('')

const categories = [
  { label: '全部', value: '' },
  { label: '颜料', value: 'paint' },
  { label: '笔', value: 'brush' },
  { label: '喷笔', value: 'airbrush' },
  { label: '旧化材料', value: 'weathering' },
  { label: '工具', value: 'tool' },
]

const categoryLabelMap: Record<string, string> = {
  paint: '颜料',
  brush: '笔',
  airbrush: '喷笔',
  weathering: '旧化材料',
  tool: '工具',
}

const filteredTools = computed(() => {
  if (!activeCategory.value) return store.tools
  return store.tools.filter(t => t.category === activeCategory.value)
})

function applyFilter() {
  const params: Record<string, string> = {}
  if (activeCategory.value) params.category = activeCategory.value
  store.fetchTools(params)
}

onMounted(() => {
  store.fetchTools()
})
</script>
