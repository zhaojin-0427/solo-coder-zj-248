<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h2 class="section-title">板件市场</h2>
      <router-link to="/market/publish" class="kit-btn-primary flex items-center gap-2">
        <Plus :size="16" />
        发布交易
      </router-link>
    </div>

    <div class="kit-card p-4 mb-6 flex flex-wrap items-center gap-4">
      <div class="flex items-center gap-1">
        <button
          v-for="t in typeOptions"
          :key="t.value"
          class="kit-btn text-xs"
          :class="filters.type === t.value ? 'kit-btn-primary' : 'kit-btn-secondary'"
          @click="filters.type = t.value; applyFilters()"
        >
          {{ t.label }}
        </button>
      </div>
      <select v-model="filters.scale" class="kit-select text-xs" @change="applyFilters()">
        <option value="">全部比例</option>
        <option v-for="s in scaleOptions" :key="s" :value="s">{{ s }}</option>
      </select>
      <select v-model="filters.manufacturer" class="kit-select text-xs" @change="applyFilters()">
        <option value="">全部厂商</option>
        <option v-for="m in manufacturerOptions" :key="m" :value="m">{{ m }}</option>
      </select>
      <select v-model="filters.subject" class="kit-select text-xs" @change="applyFilters()">
        <option value="">全部题材</option>
        <option v-for="s in subjectOptions" :key="s" :value="s">{{ s }}</option>
      </select>
    </div>

    <div v-if="store.loading" class="text-center py-20 text-gray-500">加载中...</div>
    <div v-else-if="store.listings.length === 0" class="text-center py-20 text-gray-500">暂无板件信息</div>
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="listing in store.listings"
        :key="listing.id"
        class="kit-card cursor-pointer"
        @click="goDetail(listing.id)"
      >
        <div class="p-4">
          <div class="flex items-center justify-between mb-2">
            <span class="military-id">KIT-{{ String(listing.id).padStart(3, '0') }}</span>
            <span
              class="kit-tag text-xs"
              :class="listing.type === 'sell' ? 'kit-tag-olive' : 'kit-tag-rust'"
            >
              {{ listing.type === 'sell' ? '出售' : '求购' }}
            </span>
          </div>
          <h3 class="font-display font-semibold text-military-sand text-base mb-2 line-clamp-1">{{ listing.title }}</h3>
          <div class="flex flex-wrap gap-1 mb-3">
            <span class="kit-tag-steel text-xs">{{ listing.scale }}</span>
            <span class="kit-tag-sand text-xs">{{ listing.manufacturer }}</span>
            <span class="kit-tag-olive text-xs">{{ conditionLabel(listing.condition) }}</span>
          </div>
          <div v-if="listing.missing_parts" class="flex items-center gap-1 mb-2 text-military-rust-light text-xs">
            <AlertTriangle :size="12" />
            <span>缺件: {{ listing.missing_parts }}</span>
          </div>
          <div class="flex items-center justify-between mt-3 pt-3 border-t border-military-olive/10">
            <span class="font-display text-lg font-bold text-military-sand">¥{{ listing.price }}</span>
            <div class="flex items-center gap-2 text-xs text-gray-500">
              <User :size="12" />
              <span>玩家#{{ listing.user_id }}</span>
              <span class="ml-2">{{ listing.created_at?.slice(0, 10) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, AlertTriangle, User } from 'lucide-vue-next'
import { useMarketStore } from '@/stores/market'

const store = useMarketStore()
const router = useRouter()

const typeOptions = [
  { label: '全部', value: '' },
  { label: '出售', value: 'sell' },
  { label: '求购', value: 'buy' },
]
const scaleOptions = ['1/35', '1/48', '1/72', '1/144', '1/350']
const manufacturerOptions = ['田宫', '长谷川', '威龙', '号手', '小号手', 'Meng', 'AFV Club', 'Italeri']
const subjectOptions = ['坦克', '战斗机', '战舰', '通用技巧']

function conditionLabel(c: string) {
  const map: Record<string, string> = { sealed: '全新未拆', opened: '已拆封', partial: '部分零件', damaged: '有损伤' }
  return map[c] || c
}

const filters = reactive({
  type: '',
  scale: '',
  manufacturer: '',
  subject: '',
})

function applyFilters() {
  const params: Record<string, string> = {}
  if (filters.type) params.type = filters.type
  if (filters.scale) params.scale = filters.scale
  if (filters.manufacturer) params.manufacturer = filters.manufacturer
  if (filters.subject) params.subject = filters.subject
  store.fetchListings(params)
}

function goDetail(id: number) {
  router.push(`/market/detail/${id}`)
}

onMounted(() => {
  store.fetchListings()
})
</script>
