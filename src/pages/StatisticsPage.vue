<template>
  <div>
    <h2 class="section-title mb-6">数据统计</h2>

    <div v-if="store.loading" class="text-center py-20 text-gray-500">加载中...</div>
    <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="kit-card p-5">
        <h3 class="font-display font-semibold text-military-sand tracking-wide mb-3">热门题材</h3>
        <div class="flex gap-2 mb-4">
          <button
            v-for="s in scaleTabs"
            :key="s"
            class="kit-btn text-xs"
            :class="subjectScale === s ? 'kit-btn-primary' : 'kit-btn-secondary'"
            @click="subjectScale = s"
          >
            {{ s }}
          </button>
        </div>
        <v-chart :option="subjectOption" autoresize style="height: 280px" />
      </div>

      <div class="kit-card p-5">
        <h3 class="font-display font-semibold text-military-sand tracking-wide mb-3">流转速度</h3>
        <v-chart :option="turnoverOption" autoresize style="height: 280px" />
      </div>

      <div class="kit-card p-5">
        <h3 class="font-display font-semibold text-military-sand tracking-wide mb-3">教程完播率</h3>
        <v-chart :option="completionOption" autoresize style="height: 280px" />
      </div>

      <div class="kit-card p-5">
        <h3 class="font-display font-semibold text-military-sand tracking-wide mb-3">技法收藏排行</h3>
        <v-chart :option="favoriteOption" autoresize style="height: 280px" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { useStatisticsStore } from '@/stores/statistics'

use([BarChart, LineChart, PieChart, TitleComponent, TooltipComponent, GridComponent, LegendComponent, CanvasRenderer])

const store = useStatisticsStore()
const subjectScale = ref('1/35')
const scaleTabs = ['1/35', '1/48', '1/72', '1/144', '1/350']

const subjectOption = computed(() => {
  const data = store.subjectStats.filter(s => s.scale === subjectScale.value)
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    grid: { left: 60, right: 20, top: 10, bottom: 30 },
    xAxis: {
      type: 'category',
      data: data.map(d => d.subject),
      axisLabel: { color: '#999', fontSize: 11 },
      axisLine: { lineStyle: { color: '#4A5D2330' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#999', fontSize: 11 },
      splitLine: { lineStyle: { color: '#4A5D2320' } },
    },
    series: [{
      type: 'bar',
      data: data.map(d => d.count),
      itemStyle: { color: '#4A5D23', borderRadius: [4, 4, 0, 0] },
      barWidth: '50%',
    }],
  }
})

const turnoverOption = computed(() => ({
  backgroundColor: 'transparent',
  tooltip: { trigger: 'axis' },
  grid: { left: 50, right: 20, top: 10, bottom: 30 },
  xAxis: {
    type: 'category',
    data: store.turnoverStats.map(d => d.month),
    axisLabel: { color: '#999', fontSize: 11 },
    axisLine: { lineStyle: { color: '#4A5D2330' } },
  },
  yAxis: {
    type: 'value',
    name: '平均天数',
    nameTextStyle: { color: '#999', fontSize: 11 },
    axisLabel: { color: '#999', fontSize: 11 },
    splitLine: { lineStyle: { color: '#4A5D2320' } },
  },
  series: [
    { type: 'line', data: store.turnoverStats.map(d => d.avg_days), lineStyle: { color: '#4A5D23' }, itemStyle: { color: '#4A5D23' }, smooth: true },
  ],
}))

const completionOption = computed(() => {
  const data = store.completionStats.map(d => ({
    name: d.title,
    value: d.completion_rate,
    views: d.views,
    completions: d.completions,
  }))
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        const item = data[params.dataIndex]
        return `${item.name}<br/>完播率: ${item.value}%<br/>浏览: ${item.views}<br/>完成: ${item.completions}`
      },
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      textStyle: { color: '#999', fontSize: 11 },
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['35%', '50%'],
      avoidLabelOverlap: false,
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold', color: '#D4A843' } },
      data: data.map((d, i) => ({
        name: d.name,
        value: d.value,
        itemStyle: {
          color: ['#4A7A2E', '#D4A843', '#8B3A2A', '#4A5D23', '#6B8E23'][i % 5],
        },
      })),
    }],
  }
})

const favoriteOption = computed(() => {
  const data = store.favoriteStats.slice(0, 10)
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    grid: { left: 80, right: 20, top: 10, bottom: 20 },
    xAxis: {
      type: 'value',
      axisLabel: { color: '#999', fontSize: 11 },
      splitLine: { lineStyle: { color: '#4A5D2320' } },
    },
    yAxis: {
      type: 'category',
      data: data.map(d => d.technique),
      axisLabel: { color: '#999', fontSize: 11 },
      axisLine: { lineStyle: { color: '#4A5D2330' } },
    },
    series: [{
      type: 'bar',
      data: data.map(d => d.favorite_count),
      itemStyle: { color: '#D4A843', borderRadius: [0, 4, 4, 0] },
      barWidth: '60%',
    }],
  }
})

onMounted(() => {
  store.fetchAll()
})
</script>
