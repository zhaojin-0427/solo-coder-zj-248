<template>
  <div>
    <div class="flex items-center gap-3 mb-6">
      <button class="kit-btn-secondary text-xs" @click="router.back()">
        <ArrowLeft :size="14" class="inline mr-1" />返回
      </button>
      <h2 class="section-title">板件详情</h2>
    </div>

    <div v-if="store.loading" class="text-center py-20 text-gray-500">加载中...</div>
    <template v-else-if="store.currentListing">
      <div class="kit-card p-6 mb-6">
        <div class="flex items-center justify-between mb-4">
          <span class="military-id">KIT-{{ String(store.currentListing.id).padStart(3, '0') }}</span>
          <div class="flex items-center gap-2">
            <span
              class="kit-tag text-xs"
              :class="store.currentListing.type === 'sell' ? 'kit-tag-olive' : 'kit-tag-rust'"
            >
              {{ store.currentListing.type === 'sell' ? '出售' : '求购' }}
            </span>
            <span class="kit-tag-steel text-xs">{{ store.currentListing.status || '进行中' }}</span>
          </div>
        </div>

        <h3 class="font-display text-xl font-bold text-military-sand mb-4">{{ store.currentListing.title }}</h3>

        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <div class="bg-military-bg rounded p-3">
            <div class="text-xs text-gray-500 font-display mb-1">比例</div>
            <div class="text-sm text-gray-200">{{ store.currentListing.scale }}</div>
          </div>
          <div class="bg-military-bg rounded p-3">
            <div class="text-xs text-gray-500 font-display mb-1">厂商</div>
            <div class="text-sm text-gray-200">{{ store.currentListing.manufacturer }}</div>
          </div>
          <div class="bg-military-bg rounded p-3">
            <div class="text-xs text-gray-500 font-display mb-1">品相</div>
            <div class="text-sm text-gray-200">{{ conditionLabel(store.currentListing.condition) }}</div>
          </div>
          <div class="bg-military-bg rounded p-3">
            <div class="text-xs text-gray-500 font-display mb-1">题材</div>
            <div class="text-sm text-gray-200">{{ store.currentListing.subject }}</div>
          </div>
        </div>

        <div class="bg-military-bg rounded p-4 mb-4">
          <div class="text-xs text-gray-500 font-display mb-2">描述</div>
          <div class="text-sm text-gray-300 leading-relaxed">{{ store.currentListing.description || '暂无描述' }}</div>
        </div>

        <div v-if="store.currentListing.missing_parts" class="bg-military-rust/10 border border-military-rust/30 rounded p-4 mb-4">
          <div class="flex items-center gap-2 text-military-rust-light text-xs font-display mb-2">
            <AlertTriangle :size="14" />
            缺件信息
          </div>
          <div class="text-sm text-gray-300">{{ store.currentListing.missing_parts }}</div>
        </div>

        <div class="flex items-center justify-between pt-4 border-t border-military-olive/10">
          <div class="font-display text-2xl font-bold text-military-sand">¥{{ store.currentListing.price }}</div>
          <div class="flex items-center gap-2 text-sm text-gray-500">
            <User :size="14" />
            <span>玩家#{{ store.currentListing.user_id }}</span>
            <span class="text-gray-600">|</span>
            <Calendar :size="14" />
            <span>{{ store.currentListing.created_at?.slice(0, 10) }}</span>
          </div>
        </div>
      </div>

      <div class="kit-card p-6">
        <h3 class="font-display font-semibold text-military-sand tracking-wide mb-4 flex items-center gap-2">
          <GitMerge :size="16" />
          匹配结果
        </h3>
        <div v-if="store.matches.length === 0" class="text-center py-8 text-gray-500 text-sm">暂无匹配结果</div>
        <div v-else class="space-y-3">
          <div
            v-for="match in store.matches"
            :key="match.id"
            class="bg-military-bg rounded p-4 flex items-center justify-between"
          >
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-1">
                <span class="military-id">匹配 #{{ match.id }}</span>
                <span
                  class="kit-tag text-xs"
                  :class="store.currentListing?.type === 'sell' ? 'kit-tag-rust' : 'kit-tag-olive'"
                >
                  {{ store.currentListing?.type === 'sell' ? '求购方' : '出售方' }}
                </span>
              </div>
              <div class="text-xs text-gray-500">
                {{ store.currentListing?.type === 'sell' ? `求购挂单 #${match.buy_listing_id}` : `出售挂单 #${match.sell_listing_id}` }}
              </div>
            </div>
            <div class="flex items-center gap-2">
              <div class="w-20 h-2 bg-military-bg-card rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full transition-all"
                  :class="match.match_score >= 80 ? 'bg-military-olive' : match.match_score >= 50 ? 'bg-military-sand' : 'bg-military-rust'"
                  :style="{ width: match.match_score + '%' }"
                ></div>
              </div>
              <span class="text-xs text-gray-400 font-display">{{ match.match_score }}%</span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, AlertTriangle, User, Calendar, GitMerge } from 'lucide-vue-next'
import { useMarketStore } from '@/stores/market'

const route = useRoute()
const router = useRouter()
const store = useMarketStore()
const id = Number(route.params.id)

function conditionLabel(c: string) {
  const map: Record<string, string> = { sealed: '全新未拆', opened: '已拆封', partial: '部分零件', damaged: '有损伤' }
  return map[c] || c
}

onMounted(() => {
  store.fetchListingDetail(id)
  store.fetchMatches(id)
})
</script>
