<template>
  <div class="dashboard-container" v-loading="loading">
    
    <!-- Top Stats Row -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-title">全网知识图谱节点总数</div>
          <div class="stat-value" style="color: #6366f1;">{{ summary.total_nodes }}</div>
          <div class="stat-desc">涵盖疾病、症状、干预方案等核心实体</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-title">今日活跃咨询会话</div>
          <div class="stat-value" style="color: #10b981;">{{ summary.today_sessions }}</div>
          <div class="stat-desc">系统累计已承接 {{ summary.total_sessions }} 轮干预</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-title">高危预警拦截总数</div>
          <div class="stat-value" style="color: #ef4444;">{{ summary.total_alerts }}</div>
          <div class="stat-desc">基于 RAG 安全熔断机制</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-title">当前待处理危机工单</div>
          <div class="stat-value" style="color: #f59e0b;">{{ summary.pending_alerts }}</div>
          <div class="stat-desc">请立刻前往【高危预警处理】跟进！</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="charts-row">
      <!-- Line Chart: Alert Trends -->
      <el-col :span="14">
        <el-card shadow="never" class="chart-card">
          <template #header>近 7 天高危干预趋势 (次)</template>
          <v-chart class="chart" :option="trendOption" autoresize />
        </el-card>
      </el-col>

      <!-- Bar Chart: Top Symptoms -->
      <el-col :span="10">
        <el-card shadow="never" class="chart-card">
          <template #header>触发最频繁的高危核型 Top 10</template>
          <v-chart class="chart" :option="symptomOption" autoresize />
        </el-card>
      </el-col>
    </el-row>

    <!-- KGraph Stats Row -->
    <el-row :gutter="20" class="charts-row">
      <!-- Pie Chart: Node Distribution -->
      <el-col :span="12">
        <el-card shadow="never" class="chart-card">
          <template #header>图谱实体分布 (Node Types)</template>
          <v-chart class="chart" :option="nodeOption" autoresize />
        </el-card>
      </el-col>

      <!-- Pie Chart: Relationship Distribution -->
      <el-col :span="12">
        <el-card shadow="never" class="chart-card">
          <template #header>图谱关系链路分布 (Relationship Types)</template>
          <v-chart class="chart" :option="relOption" autoresize />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent } from 'echarts/components'
import VChart, { THEME_KEY } from 'vue-echarts'
import { provide } from 'vue'
import apiClient from '../utils/api'
import { ElMessage } from 'element-plus'

use([
  CanvasRenderer,
  LineChart,
  BarChart,
  PieChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent
])

// Optional theme
provide(THEME_KEY, 'light')

const loading = ref(true)

const summary = ref({
  total_nodes: 0,
  today_sessions: 0,
  total_sessions: 0,
  total_alerts: 0,
  pending_alerts: 0
})

const trendData = ref({ dates: [], counts: [] })
const topSymptoms = ref([])
const graphStats = ref({ nodes: [], relationships: [] })

const fetchDashboardStats = async () => {
  loading.value = true
  try {
    const res: any = await apiClient.get('/dashboard/stats/')
    // ApiClient interceptor currently returns response directly
    summary.value = res.summary
    trendData.value = res.trends
    topSymptoms.value = res.top_symptoms
    graphStats.value = res.graph_stats || { nodes: [], relationships: [] }
  } catch (e) {
    ElMessage.error('无法拉取大盘聚合数据')
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchDashboardStats()
})

const trendOption = computed(() => {
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '5%', containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: trendData.value.dates,
      axisLine: { lineStyle: { color: '#ccc' } }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { type: 'dashed', color: '#eee' } }
    },
    series: [
      {
        name: '拦截次数',
        type: 'line',
        data: trendData.value.counts,
        smooth: true,
        itemStyle: { color: '#ef4444' },
        areaStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(239, 68, 68, 0.3)' },
              { offset: 1, color: 'rgba(239, 68, 68, 0.05)' }
            ]
          }
        }
      }
    ]
  }
})

const symptomOption = computed(() => {
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '4%', bottom: '5%', containLabel: true },
    xAxis: {
      type: 'value',
      splitLine: { lineStyle: { type: 'dashed', color: '#eee' } }
    },
    yAxis: {
      type: 'category',
      data: topSymptoms.value.map((s: any) => s.name).reverse(),
      axisLine: { lineStyle: { color: '#ccc' } }
    },
    series: [
      {
        name: '触发频次',
        type: 'bar',
        data: topSymptoms.value.map((s: any) => s.value).reverse(),
        itemStyle: {
          color: '#3b82f6',
          borderRadius: [0, 4, 4, 0]
        }
      }
    ]
  }
})

const nodeOption = computed(() => {
  return {
    tooltip: { trigger: 'item', formatter: '{a} <br/>{b}: {c} ({d}%)' },
    legend: { orient: 'vertical', right: 10, top: 'center' },
    series: [
      {
        name: '节点分布',
        type: 'pie',
        radius: ['45%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
        label: { show: false, position: 'center' },
        emphasis: { label: { show: true, fontSize: 16, fontWeight: 'bold' } },
        labelLine: { show: false },
        data: graphStats.value.nodes
      }
    ]
  }
})

const relOption = computed(() => {
  return {
    tooltip: { trigger: 'item', formatter: '{a} <br/>{b}: {c} ({d}%)' },
    legend: { orient: 'vertical', right: 10, top: 'center' },
    series: [
      {
        name: '关系链路',
        type: 'pie',
        radius: ['45%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
        label: { show: false, position: 'center' },
        emphasis: { label: { show: true, fontSize: 16, fontWeight: 'bold' } },
        labelLine: { show: false },
        data: graphStats.value.relationships
      }
    ]
  }
})
</script>

<style scoped>
.dashboard-container {
  padding: 10px;
  overflow-x: hidden;
}
.stats-row {
  margin-bottom: 20px;
}

/* 深度选择器穿透，强制去掉 Element Plus 卡片内部的滚动条 */
:deep(.el-card) {
  overflow: hidden !important;
  border: none;
  box-shadow: var(--shadow-sm) !important;
}

:deep(.el-card__body) {
  padding: 20px !important;
  height: 100%;
  box-sizing: border-box;
  overflow: hidden !important; /* 核心修复：强制切断内部溢出 */
}

.stat-card {
  height: 140px;
}

/* 指标卡内部布局优化 */
.stat-card :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.stat-title {
  font-size: 14px;
  color: #64748b;
  margin-bottom: 8px;
  font-weight: 500;
}
.stat-value {
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 4px;
}
.stat-desc {
  font-size: 12px;
  color: #94a3b8;
}
.charts-row {
  margin-top: 20px;
}
.chart-card {
  height: 400px;
}
.chart {
  width: 100%;
  height: 320px;
}
</style>
