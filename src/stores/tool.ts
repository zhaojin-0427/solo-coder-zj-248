import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Tool } from '@/types'
import { getTools, getToolDetail } from '@/api'

export const useToolStore = defineStore('tool', () => {
  const tools = ref<Tool[]>([])
  const currentTool = ref<Tool | null>(null)
  const loading = ref(false)

  async function fetchTools(params?: Record<string, string>) {
    loading.value = true
    try {
      tools.value = await getTools(params)
    } finally {
      loading.value = false
    }
  }

  async function fetchToolDetail(id: number) {
    loading.value = true
    try {
      currentTool.value = await getToolDetail(id)
    } finally {
      loading.value = false
    }
  }

  return { tools, currentTool, loading, fetchTools, fetchToolDetail }
})
