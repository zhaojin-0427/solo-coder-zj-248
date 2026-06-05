<template>
  <div>
    <div class="flex items-center gap-3 mb-6">
      <button class="kit-btn-secondary text-xs" @click="router.back()">
        <ArrowLeft :size="14" class="inline mr-1" />返回
      </button>
      <h2 class="section-title">发布交易</h2>
    </div>

    <form @submit.prevent="handleSubmit" class="max-w-2xl space-y-6">
      <div class="kit-card p-5">
        <div class="flex items-center gap-2 mb-4">
          <div class="w-6 h-6 rounded-full bg-military-olive flex items-center justify-center text-white text-xs font-display font-bold">1</div>
          <h3 class="font-display font-semibold text-military-sand tracking-wide">基本信息</h3>
        </div>
        <div class="space-y-4">
          <div>
            <label class="block text-xs text-gray-400 mb-1 font-display">标题</label>
            <input v-model="form.title" class="kit-input w-full" placeholder="输入板件标题" />
          </div>
          <div>
            <label class="block text-xs text-gray-400 mb-1 font-display">交易类型</label>
            <div class="flex gap-3">
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="radio" v-model="form.type" value="sell" class="accent-military-olive" />
                <span class="text-sm text-gray-300">出售</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="radio" v-model="form.type" value="buy" class="accent-military-rust" />
                <span class="text-sm text-gray-300">求购</span>
              </label>
            </div>
          </div>
          <div>
            <label class="block text-xs text-gray-400 mb-1 font-display">价格</label>
            <input v-model.number="form.price" type="number" class="kit-input w-full" placeholder="0.00" />
          </div>
          <div>
            <label class="block text-xs text-gray-400 mb-1 font-display">描述</label>
            <textarea v-model="form.description" class="kit-input w-full h-24 resize-none" placeholder="详细描述板件状态"></textarea>
          </div>
        </div>
      </div>

      <div class="kit-card p-5">
        <div class="flex items-center gap-2 mb-4">
          <div class="w-6 h-6 rounded-full bg-military-olive flex items-center justify-center text-white text-xs font-display font-bold">2</div>
          <h3 class="font-display font-semibold text-military-sand tracking-wide">板件属性</h3>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-xs text-gray-400 mb-1 font-display">比例</label>
            <select v-model="form.scale" class="kit-select w-full">
              <option value="">选择比例</option>
              <option v-for="s in scaleOptions" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
          <div>
            <label class="block text-xs text-gray-400 mb-1 font-display">厂商</label>
            <input v-model="form.manufacturer" class="kit-input w-full" placeholder="输入厂商名称" />
          </div>
          <div>
            <label class="block text-xs text-gray-400 mb-1 font-display">品相</label>
            <select v-model="form.condition" class="kit-select w-full">
              <option value="">选择品相</option>
              <option value="sealed">全新未拆</option>
              <option value="opened">全新拆封</option>
              <option value="partial">部分零件</option>
              <option value="damaged">有损伤</option>
            </select>
          </div>
          <div>
            <label class="block text-xs text-gray-400 mb-1 font-display">题材</label>
            <select v-model="form.subject" class="kit-select w-full">
              <option value="">选择题材</option>
              <option v-for="s in subjectOptions" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
        </div>
      </div>

      <div class="kit-card p-5">
        <div class="flex items-center gap-2 mb-4">
          <div class="w-6 h-6 rounded-full bg-military-olive flex items-center justify-center text-white text-xs font-display font-bold">3</div>
          <h3 class="font-display font-semibold text-military-sand tracking-wide">零件状态</h3>
        </div>
        <div>
          <label class="block text-xs text-gray-400 mb-1 font-display">缺件描述</label>
          <textarea v-model="form.missing_parts" class="kit-input w-full h-20 resize-none" placeholder="如有缺件请详细描述，无缺件可留空"></textarea>
        </div>
      </div>

      <div class="flex gap-3">
        <button type="submit" class="kit-btn-primary" :disabled="submitting">
          {{ submitting ? '提交中...' : '发布交易' }}
        </button>
        <button type="button" class="kit-btn-secondary" @click="router.back()">取消</button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft } from 'lucide-vue-next'
import { useMarketStore } from '@/stores/market'

const router = useRouter()
const store = useMarketStore()
const submitting = ref(false)

const scaleOptions = ['1/35', '1/48', '1/72', '1/144', '1/350']
const subjectOptions = ['坦克', '战斗机', '战舰', '通用技巧']

const form = reactive({
  title: '',
  type: 'sell' as 'sell' | 'buy',
  price: 0,
  description: '',
  scale: '',
  manufacturer: '',
  condition: '',
  subject: '',
  missing_parts: '',
  user_id: 1,
})

async function handleSubmit() {
  submitting.value = true
  try {
    await store.publishListing({ ...form, user_id: 1 })
    router.push('/market')
  } finally {
    submitting.value = false
  }
}
</script>
