<template>
  <div class="article-detail-container">
    <!-- Header -->
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="header-title">{{ isEdit ? '编辑文章' : '发布新文章' }}</span>
      </template>
      <template #extra>
        <div class="header-actions">
          <el-button @click="goBack">取消</el-button>
          <el-button type="primary" :loading="submitLoading" @click="handleSubmit">保存并提交</el-button>
        </div>
      </template>
    </el-page-header>

    <el-row :gutter="24" class="main-content">
      <!-- Left Column: Editor -->
      <el-col :span="16">
        <el-card shadow="never" class="editor-card">
          <el-form :model="form" label-position="top">
            <el-row :gutter="20">
              <el-col :span="16">
                <el-form-item label="文章标题" required>
                  <el-input v-model="form.title" placeholder="输入引人入胜的标题" size="large" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="文章作者">
                  <el-input v-model="form.author" placeholder="作者名" size="large"/>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="16">
                <el-form-item label="封面图片 URL">
                  <el-input v-model="form.cover_image" placeholder="https://example.com/image.jpg" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="发布状态">
                  <el-select v-model="form.status" style="width: 100%">
                    <el-option label="已发布" value="published" />
                    <el-option label="草案" value="draft" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="文章正文内容" required>
              <el-input
                v-model="form.content"
                type="textarea"
                :rows="25"
                placeholder="支持 Markdown 或 纯文本内容..."
                class="content-editor"
              />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- Right Column: Stats & Comments -->
      <el-col :span="8">
        <!-- Stats Card -->
        <el-card shadow="never" class="stats-card" v-if="isEdit">
          <template #header>
            <div class="card-header">
              <span>核心数据回顾 (近7天)</span>
            </div>
          </template>
          
          <div class="stats-overview">
            <div class="stat-item">
              <div class="stat-value">{{ stats.total_favorites || 0 }}</div>
              <div class="stat-label">总收藏</div>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-item">
              <div class="stat-value">{{ stats.total_comments || 0 }}</div>
              <div class="stat-label">总评论</div>
            </div>
          </div>

          <div class="chart-container">
            <v-chart class="chart" :option="chartOption" autoresize />
          </div>
        </el-card>

        <!-- Comments Card -->
        <el-card shadow="never" class="comments-card" v-if="isEdit">
          <template #header>
            <div class="card-header">
              <span>互动评论管理</span>
            </div>
          </template>
          
          <div class="comments-list" v-loading="commentsLoading">
            <div v-for="comment in comments" :key="comment.id" class="comment-item">
              <div class="comment-user">
                <el-avatar :size="32" :src="comment.user_avatar">{{ comment.user_nickname?.charAt(0) }}</el-avatar>
                <div class="user-meta">
                  <span class="nickname">{{ comment.user_nickname }}</span>
                  <span class="time">{{ formatDate(comment.created_at) }}</span>
                </div>
              </div>
              <div class="comment-content">{{ comment.content }}</div>
              <div class="comment-actions">
                <el-tag v-if="!comment.is_audit_passed" type="warning" size="small">待审核</el-tag>
                <el-button v-if="!comment.is_audit_passed" type="primary" link size="small" @click="handleAudit(comment)">通过</el-button>
                <el-button type="danger" link size="small" @click="handleDeleteComment(comment)">删除</el-button>
              </div>
            </div>
            <el-empty v-if="comments.length === 0" description="暂无评论" :image-size="60" />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import apiClient from '../utils/api'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent])

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => route.params.id !== undefined && route.params.id !== 'new')
const submitLoading = ref(false)
const commentsLoading = ref(false)

const form = ref({
  id: '',
  title: '',
  cover_image: '',
  content: '',
  author: '心理中心',
  status: 'published'
})

const stats = ref<any>({
  total_favorites: 0,
  total_comments: 0,
  daily_stats: []
})

const comments = ref<any[]>([])

const fetchArticle = async () => {
  if (!isEdit.value || !route.params.id) {
    // 初始化新文章表单
    form.value = {
      id: '',
      title: '',
      cover_image: '',
      content: '',
      author: '心理中心',
      status: 'published'
    }
    return
  }
  try {
    // 统一不加前缀斜杠以使用 axios 的 baseURL 拼接逻辑
    const res: any = await apiClient.get(`articles/${route.params.id}/`)
    form.value = { ...res }
    fetchStats()
    fetchComments()
  } catch (e) {
    ElMessage.error('获取文章详情失败')
  }
}

const fetchStats = async () => {
  if (!isEdit.value || !route.params.id) return
  try {
    const res: any = await apiClient.get(`articles/${route.params.id}/stats/`)
    stats.value = res
  } catch (e: any) {
    console.error(`获取统计失败 [ID: ${route.params.id}]:`, e.response?.status, e.message)
  }
}

const fetchComments = async () => {
  if (!isEdit.value || !route.params.id) return
  commentsLoading.value = true
  try {
    // 对应后端注册的路由 article-comments
    const res: any = await apiClient.get(`article-comments/`, {
      params: { article: route.params.id }
    })
    comments.value = Array.isArray(res) ? res : (res.results || [])
  } catch (e: any) {
    console.error(`获取评论失败 [ID: ${route.params.id}]:`, e.response?.status, e.message)
  } finally {
    commentsLoading.value = false
  }
}

const handleSubmit = async () => {
  if (!form.value.title || !form.value.content) {
    return ElMessage.warning('请填写必填项')
  }

  submitLoading.value = true
  try {
    if (isEdit.value) {
      await apiClient.put(`articles/${route.params.id}/`, form.value)
      ElMessage.success('文章更新成功')
      fetchArticle()
    } else {
      await apiClient.post('articles/', form.value)
      ElMessage.success('文章发布成功')
      router.push('/articles')
    }
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    submitLoading.value = false
  }
}

const handleAudit = async (comment: any) => {
  try {
    await apiClient.post(`article-comments/${comment.id}/audit/`, { is_passed: true })
    ElMessage.success('审核已通过')
    fetchComments()
  } catch (e) {
    ElMessage.error('审核操作失败')
  }
}

const handleDeleteComment = (comment: any) => {
  ElMessageBox.confirm('确定要永久删除这条评论吗？', '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await apiClient.delete(`article-comments/${comment.id}/`)
      ElMessage.success('评论已删除')
      fetchComments()
    } catch (e) {
      ElMessage.error('删除评论失败')
    }
  }).catch(() => {})
}

const goBack = () => {
  router.push('/articles')
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}-${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

const chartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['收藏', '评论'], bottom: 0, icon: 'circle' },
  grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true, top: '10%' },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: stats.value.daily_stats.map((d: any) => d.date)
  },
  yAxis: { type: 'value', minInterval: 1 },
  series: [
    {
      name: '收藏',
      type: 'line',
      smooth: true,
      data: stats.value.daily_stats.map((d: any) => d.favorites),
      itemStyle: { color: '#6366f1' },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [{ offset: 0, color: 'rgba(99, 102, 241, 0.2)' }, { offset: 1, color: 'transparent' }]
        }
      }
    },
    {
      name: '评论',
      type: 'line',
      smooth: true,
      data: stats.value.daily_stats.map((d: any) => d.comments),
      itemStyle: { color: '#f59e0b' }
    }
  ]
}))

onMounted(fetchArticle)

// 监听路由参数变化（处理从编辑切换到新建的情况）
watch(() => route.params.id, (newId) => {
  if (newId) fetchArticle()
})
</script>

<style scoped>
.article-detail-container {
  padding: 24px;
  background-color: #f8fafc;
  min-height: calc(100vh - 60px);
}

.page-header {
  margin-bottom: 24px;
  background: white;
  padding: 16px 24px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.header-title {
  font-weight: 600;
  color: #1e293b;
  font-size: 18px;
}

.main-content {
  margin-top: 0;
}

.editor-card, .stats-card, .comments-card {
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  color: #334155;
}

.stats-overview {
  display: flex;
  justify-content: space-around;
  align-items: center;
  padding: 10px 0 20px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #6366f1;
}

.stat-label {
  font-size: 13px;
  color: #64748b;
  margin-top: 4px;
}

.stat-divider {
  width: 1px;
  height: 40px;
  background-color: #e2e8f0;
}

.chart-container {
  height: 220px;
  margin-top: 10px;
}

.chart {
  height: 100%;
}

.comments-list {
  max-height: 600px;
  overflow-y: auto;
  padding: 4px;
}

.comment-item {
  padding: 16px 0;
  border-bottom: 1px solid #f1f5f9;
  transition: all 0.2s;
}

.comment-item:hover {
  background-color: #f8fafc;
}

.comment-item:last-child {
  border-bottom: none;
}

.comment-user {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.user-meta {
  display: flex;
  flex-direction: column;
}

.nickname {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.time {
  font-size: 12px;
  color: #94a3b8;
}

.comment-content {
  font-size: 14px;
  color: #475569;
  line-height: 1.6;
  margin-left: 44px;
  word-break: break-all;
}

.comment-actions {
  margin-top: 10px;
  margin-left: 44px;
  display: flex;
  gap: 16px;
  align-items: center;
}

.content-editor :deep(.el-textarea__inner) {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace;
  font-size: 15px;
  line-height: 1.6;
  background-color: #fdfdfd;
  padding: 20px;
  border-radius: 8px;
  color: #1e293b;
}

.content-editor :deep(.el-textarea__inner:focus) {
  background-color: #fff;
}

:deep(.el-form-item__label) {
  font-weight: 600;
  color: #475569;
}
</style>
