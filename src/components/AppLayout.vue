<template>
  <div class="flex h-screen overflow-hidden bg-military-bg font-body">
    <aside class="w-16 flex flex-col items-center py-4 bg-military-bg-card border-r border-military-olive/20 shrink-0">
      <div class="font-display text-military-sand font-bold text-lg mb-6 tracking-wider">CM</div>
      <nav class="flex flex-col gap-1 flex-1">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="flex flex-col items-center gap-0.5 py-2 px-1 rounded text-xs transition-colors"
          :class="isActive(item.path) ? 'text-military-olive bg-military-olive/10' : 'text-gray-500 hover:text-military-sand hover:bg-military-bg-hover'"
        >
          <component :is="item.icon" :size="20" />
          <span class="font-display tracking-wide leading-tight">{{ item.label }}</span>
        </router-link>
      </nav>
    </aside>
    <div class="flex flex-col flex-1 overflow-hidden">
      <header class="h-14 flex items-center px-6 bg-military-bg-card border-b border-military-olive/20 shrink-0">
        <h1 class="font-display text-xl font-bold text-military-sand tracking-widest">军模工坊</h1>
        <div class="ml-8 flex-1 max-w-md">
          <div class="relative">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" :size="16" />
            <input
              type="text"
              placeholder="搜索板件、教程、作品..."
              class="kit-input w-full pl-9"
            />
          </div>
        </div>
        <div class="ml-auto flex items-center gap-3">
          <button class="p-2 text-gray-400 hover:text-military-sand transition-colors">
            <Bell :size="18" />
          </button>
          <div class="w-8 h-8 rounded-full bg-military-olive/30 flex items-center justify-center text-military-sand font-display text-sm">
            U
          </div>
        </div>
      </header>
      <main class="flex-1 overflow-y-auto p-6">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { ShoppingCart, BookOpen, Image, Wrench, BarChart3, Search, Bell, Heart } from 'lucide-vue-next'

const route = useRoute()

const navItems = [
  { path: '/market', label: '板件市场', icon: ShoppingCart },
  { path: '/tutorials', label: '技法教程', icon: BookOpen },
  { path: '/gallery', label: '作品展示', icon: Image },
  { path: '/tools', label: '工具推荐', icon: Wrench },
  { path: '/statistics', label: '数据统计', icon: BarChart3 },
  { path: '/favorites', label: '我的收藏', icon: Heart },
]

function isActive(path: string) {
  return route.path.startsWith(path)
}
</script>
