<template>
  <div class="users-container">
    <el-card shadow="never" class="table-card">
      <template #header>
        <div class="card-header">
          <span>学生心理档案管理</span>
          <div class="header-ops">
            <el-input 
              v-model="search" 
              placeholder="搜索学号/姓名..." 
              style="width: 250px; margin-right: 15px"
              clearable
            />
            <el-button type="primary" size="small" @click="fetchUsers">刷新列表</el-button>
          </div>
        </div>
      </template>

      <el-table :data="filteredUsers" style="width: 100%" v-loading="loading" stripe>
        <el-table-column prop="campus_id" label="学号" width="120" sortable />
        <el-table-column prop="real_name" label="姓名" min-width="100">
          <template #default="scope">
            <span :class="{ 'text-placeholder': !scope.row.real_name }">
              {{ scope.row.real_name || '未填写' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="nickname" label="昵称" min-width="120">
          <template #default="scope">
            {{ scope.row.nickname || '匿名' }}
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="联系方式" width="160">
          <template #default="scope">
            <span :class="{ 'text-placeholder': !scope.row.phone }">
              {{ scope.row.phone || '未绑定' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column fixed="right" label="操作" width="140">
          <template #default="scope">
            <el-button type="primary" size="small" @click="showDetail(scope.row.id)">
              查看心理档案
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 用户侧边档案抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      :title="`心理健康档案 - ${selectedUser?.real_name || '学生详情'}`"
      size="50%"
      destroy-on-close
    >
      <div v-if="selectedUser" class="drawer-content">
        <!-- 基础资料区域 -->
        <el-descriptions title="基础身份信息" border :column="2" class="mb-lg">
          <el-descriptions-item label="学号">{{ selectedUser.campus_id }}</el-descriptions-item>
          <el-descriptions-item label="真实姓名">{{ selectedUser.real_name }}</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ selectedUser.phone || '未填写' }}</el-descriptions-item>
          <el-descriptions-item label="系统账号">{{ selectedUser.username }}</el-descriptions-item>
        </el-descriptions>

        <!-- 情绪波动曲线区域 (Echarts) -->
        <div class="section-title">每日情绪打卡轨迹 (1-5分)</div>
        <div class="chart-container">
          <v-chart v-if="selectedUser.mood_logs?.length" class="mood-chart" :option="moodChartOption" autoresize />
          <el-empty v-else description="该生暂未进行每日情绪打卡" :image-size="60" />
        </div>

        <el-divider />

        <!-- 心理测评历史 -->
        <div class="section-title">历次心理测评报告记录</div>
        <el-table :data="selectedUser.assessments" border size="small" style="width: 100%">
          <el-table-column prop="created_at" label="测评日期" width="160">
            <template #default="s">
              {{ new Date(s.row.created_at).toLocaleDateString() }}
            </template>
          </el-table-column>
          <el-table-column prop="scale_name" label="量表名称" />
          <el-table-column prop="total_score" label="得分" width="80" />
          <el-table-column prop="result_level" label="系统评估结果">
            <template #default="s">
              <el-tag :type="s.row.result_level.includes('风险') ? 'danger' : 'success'">
                {{ s.row.result_level }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { ElMessage } from 'element-plus'
import apiClient from '../utils/api'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent])

const loading = ref(false)
const search = ref('')
const users = ref([])
const drawerVisible = ref(false)
const selectedUser = ref<any>(null)

const filteredUsers = computed(() => {
  return users.value.filter((u: any) => 
    u.real_name?.includes(search.value) || u.campus_id?.includes(search.value)
  )
})

const fetchUsers = async () => {
  loading.value = true
  try {
    const res: any = await apiClient.get('/users/')
    users.value = res
  } catch (e) {
    ElMessage.error('获取学生列表失败')
  } finally {
    loading.value = false
  }
}

const showDetail = async (id: string) => {
  try {
    const res: any = await apiClient.get(`/users/${id}/`)
    selectedUser.value = res
    drawerVisible.value = true
  } catch (e) {
    ElMessage.error('拉取详细档案失败')
  }
}

const moodChartOption = computed(() => {
  if (!selectedUser.value?.mood_logs?.length) return {}
  const logs = [...selectedUser.value.mood_logs].reverse() // 升序排列
  return {
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: logs.map((l: any) => l.created_at),
      axisLabel: { color: '#94a3b8' }
    },
    yAxis: {
      type: 'value',
      min: 1,
      max: 5,
      interval: 1,
      name: '心情分',
      splitLine: { lineStyle: { type: 'dashed' } }
    },
    series: [{
      data: logs.map((l: any) => l.mood_level),
      type: 'line',
      smooth: true,
      itemStyle: { color: '#10b981' },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [{ offset: 0, color: 'rgba(16, 185, 129, 0.4)' }, { offset: 1, color: 'rgba(16, 185, 129, 0.05)' }]
        }
      }
    }]
  }
})

onMounted(fetchUsers)
</script>

<style scoped>
.users-container {
  padding: 10px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header-ops {
  display: flex;
  align-items: center;
}
.mb-lg {
  margin-bottom: 24px;
}
.drawer-content {
  padding: 0 10px;
}
.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 20px 0 12px;
  display: flex;
  align-items: center;
}
.section-title::before {
  content: "";
  width: 4px;
  height: 16px;
  background-color: #0891b2;
  margin-right: 8px;
  border-radius: 2px;
}
.chart-container {
  height: 260px;
  width: 100%;
}
.mood-chart {
  height: 100%;
}
.text-placeholder {
  color: #94a3b8;
  font-style: italic;
  font-size: 13px;
}
</style>
