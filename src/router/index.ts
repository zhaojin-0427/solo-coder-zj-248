import { createRouter, createWebHistory } from 'vue-router'
import MarketPage from '@/pages/MarketPage.vue'
import MarketPublishPage from '@/pages/MarketPublishPage.vue'
import MarketDetailPage from '@/pages/MarketDetailPage.vue'
import TutorialPage from '@/pages/TutorialPage.vue'
import TutorialDetailPage from '@/pages/TutorialDetailPage.vue'
import TutorialPublishPage from '@/pages/TutorialPublishPage.vue'
import GalleryPage from '@/pages/GalleryPage.vue'
import GalleryDetailPage from '@/pages/GalleryDetailPage.vue'
import ToolsPage from '@/pages/ToolsPage.vue'
import StatisticsPage from '@/pages/StatisticsPage.vue'
import FavoritesPage from '@/pages/FavoritesPage.vue'

const routes: import('vue-router').RouteRecordRaw[] = [
  { path: '/', redirect: '/market' },
  { path: '/market', name: 'market', component: MarketPage },
  { path: '/market/publish', name: 'market-publish', component: MarketPublishPage },
  { path: '/market/detail/:id', name: 'market-detail', component: MarketDetailPage },
  { path: '/tutorials', name: 'tutorials', component: TutorialPage },
  { path: '/tutorials/:id', name: 'tutorial-detail', component: TutorialDetailPage },
  { path: '/tutorials/publish', name: 'tutorial-publish', component: TutorialPublishPage },
  { path: '/gallery', name: 'gallery', component: GalleryPage },
  { path: '/gallery/:id', name: 'gallery-detail', component: GalleryDetailPage },
  { path: '/tools', name: 'tools', component: ToolsPage },
  { path: '/statistics', name: 'statistics', component: StatisticsPage },
  { path: '/favorites', name: 'favorites', component: FavoritesPage },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
