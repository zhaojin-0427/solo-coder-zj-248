<template>
  <div>
    <div class="flex items-center gap-3 mb-6">
      <button class="kit-btn-secondary text-xs" @click="router.back()">
        <ArrowLeft :size="14" class="inline mr-1" />返回
      </button>
      <h2 class="section-title">发布教程</h2>
    </div>

    <form @submit.prevent="handleSubmit" class="max-w-2xl space-y-6">
      <div class="kit-card p-5">
        <h3 class="font-display font-semibold text-military-sand tracking-wide mb-4">基本信息</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-xs text-gray-400 mb-1 font-display">标题</label>
            <input v-model="form.title" class="kit-input w-full" placeholder="输入教程标题" />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs text-gray-400 mb-1 font-display">题材</label>
              <select v-model="form.subject" class="kit-select w-full">
                <option value="">选择题材</option>
                <option v-for="s in subjectOptions" :key="s" :value="s">{{ s }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs text-gray-400 mb-1 font-display">难度</label>
              <select v-model="form.difficulty" class="kit-select w-full">
                <option value="beginner">入门</option>
                <option value="intermediate">进阶</option>
                <option value="advanced">大师</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <div class="kit-card p-5">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-display font-semibold text-military-sand tracking-wide">制作步骤</h3>
          <button type="button" class="kit-btn-secondary text-xs flex items-center gap-1" @click="addStep">
            <Plus :size="12" />添加步骤
          </button>
        </div>
        <div class="space-y-3">
          <div v-for="(step, i) in form.steps" :key="i" class="bg-military-bg rounded p-3">
            <div class="flex items-center justify-between mb-2">
              <span class="military-id">步骤 {{ i + 1 }}</span>
              <button type="button" class="text-military-rust-light hover:text-military-rust text-xs" @click="removeStep(i)">
                <Trash2 :size="14" />
              </button>
            </div>
            <div class="space-y-2">
              <input v-model="step.title" class="kit-input w-full text-xs" placeholder="步骤标题" />
              <textarea v-model="step.description" class="kit-input w-full text-xs h-16 resize-none" placeholder="步骤描述"></textarea>
              <input v-model="step.technique" class="kit-input w-full text-xs" placeholder="使用技法" />
            </div>
          </div>
        </div>
      </div>

      <div class="kit-card p-5">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-display font-semibold text-military-sand tracking-wide">使用颜料</h3>
          <button type="button" class="kit-btn-secondary text-xs flex items-center gap-1" @click="addPaint">
            <Plus :size="12" />添加颜料
          </button>
        </div>
        <div class="space-y-3">
          <div v-for="(paint, i) in form.paints" :key="i" class="bg-military-bg rounded p-3">
            <div class="flex items-center justify-between mb-2">
              <span class="military-id">颜料 {{ i + 1 }}</span>
              <button type="button" class="text-military-rust-light hover:text-military-rust text-xs" @click="removePaint(i)">
                <Trash2 :size="14" />
              </button>
            </div>
            <div class="grid grid-cols-2 gap-2">
              <input v-model="paint.name" class="kit-input text-xs" placeholder="颜料名称" />
              <input v-model="paint.brand" class="kit-input text-xs" placeholder="品牌" />
              <input v-model="paint.color_code" class="kit-input text-xs" placeholder="色号" />
              <input v-model="paint.usage" class="kit-input text-xs" placeholder="用途" />
            </div>
          </div>
        </div>
      </div>

      <div class="kit-card p-5">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-display font-semibold text-military-sand tracking-wide">旧化技法</h3>
          <button type="button" class="kit-btn-secondary text-xs flex items-center gap-1" @click="addWeathering">
            <Plus :size="12" />添加旧化
          </button>
        </div>
        <div class="space-y-3">
          <div v-for="(w, i) in form.weathering" :key="i" class="bg-military-bg rounded p-3">
            <div class="flex items-center justify-between mb-2">
              <span class="military-id">旧化 {{ i + 1 }}</span>
              <button type="button" class="text-military-rust-light hover:text-military-rust text-xs" @click="removeWeathering(i)">
                <Trash2 :size="14" />
              </button>
            </div>
            <div class="space-y-2">
              <input v-model="w.type" class="kit-input w-full text-xs" placeholder="旧化类型 (如: 流锈, 掉漆)" />
              <input v-model="w.productsStr" class="kit-input w-full text-xs" placeholder="使用产品 (逗号分隔)" />
              <input v-model="w.technique" class="kit-input w-full text-xs" placeholder="技法描述" />
              <textarea v-model="w.description" class="kit-input w-full text-xs h-14 resize-none" placeholder="详细说明"></textarea>
            </div>
          </div>
        </div>
      </div>

      <div class="flex gap-3">
        <button type="submit" class="kit-btn-primary" :disabled="submitting">
          {{ submitting ? '提交中...' : '发布教程' }}
        </button>
        <button type="button" class="kit-btn-secondary" @click="router.back()">取消</button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Plus, Trash2 } from 'lucide-vue-next'
import { useTutorialStore } from '@/stores/tutorial'

interface StepForm { title: string; description: string; technique: string }
interface PaintForm { name: string; brand: string; color_code: string; usage: string }
interface WeatheringForm { type: string; productsStr: string; technique: string; description: string }

const router = useRouter()
const store = useTutorialStore()
const submitting = ref(false)

const subjectOptions = ['坦克', '战斗机', '战舰', '通用技巧']

const form = reactive({
  title: '',
  subject: '',
  difficulty: 'beginner' as 'beginner' | 'intermediate' | 'advanced',
  steps: [] as StepForm[],
  paints: [] as PaintForm[],
  weathering: [] as WeatheringForm[],
})

function addStep() {
  form.steps.push({ title: '', description: '', technique: '' })
}

function removeStep(i: number) {
  form.steps.splice(i, 1)
}

function addPaint() {
  form.paints.push({ name: '', brand: '', color_code: '', usage: '' })
}

function removePaint(i: number) {
  form.paints.splice(i, 1)
}

function addWeathering() {
  form.weathering.push({ type: '', productsStr: '', technique: '', description: '' })
}

function removeWeathering(i: number) {
  form.weathering.splice(i, 1)
}

async function handleSubmit() {
  submitting.value = true
  try {
    await store.publishTutorial({
      user_id: 1,
      title: form.title,
      subject: form.subject,
      difficulty: form.difficulty,
      steps: form.steps.map((s, i) => ({
        id: 0,
        tutorial_id: 0,
        order_num: i + 1,
        title: s.title,
        description: s.description,
        technique: s.technique,
        image: '',
      })),
      paints: form.paints.map(p => ({
        id: 0,
        tutorial_id: 0,
        name: p.name,
        brand: p.brand,
        color_code: p.color_code,
        usage: p.usage,
      })),
      weathering_details: form.weathering.map(w => ({
        id: 0,
        tutorial_id: 0,
        type: w.type,
        products: w.productsStr.split(',').map(s => s.trim()).filter(Boolean),
        technique: w.technique,
        description: w.description,
      })),
    })
    router.push('/tutorials')
  } catch (error: any) {
    console.error('发布失败:', error)
    alert('发布失败：' + (error?.response?.data?.detail || error?.message || '未知错误'))
  } finally {
    submitting.value = false
  }
}
</script>
