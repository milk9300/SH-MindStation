<template>
  <div class="articles-container">
    <el-card shadow="never" class="header-card">
      <div class="header-content">
        <div class="title-section">
          <h3>科普文章内容管理</h3>
          <p class="subtitle">管理图谱推荐的科普文章，支持富文本内容与 UUID 关联</p>
        </div>
        <el-button type="primary" :icon="Plus" @click="handleAdd">发布新文章</el-button>
      </div>
    </el-card>

    <div class="articles-grid" v-loading="loading">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in articles" :key="item.id">
          <el-card shadow="hover" :body-style="{ padding: '0px' }" class="article-card">
            <div class="card-cover" :style="{ backgroundImage: `url(${item.cover_image || '/default-article.jpg'})` }">
              <div class="card-tag">{{ item.status === 'published' ? '已发布' : '草稿' }}</div>
            </div>
            <div class="card-info">
              <h4 class="article-title">{{ item.title }}</h4>
              <p class="article-meta">作者: {{ item.author }} | ID: {{ item.id }}</p>
              <div class="card-actions">
                <el-button type="primary" link :icon="Edit" @click="handleEdit(item)">编辑</el-button>
                <el-button type="danger" link :icon="Delete" @click="handleDelete(item)">删除</el-button>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      <el-empty v-if="articles.length === 0 && !loading" description="暂无文章内容" />
    </div>

    <!-- 编辑抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      :title="isEdit ? '编辑文章' : '发布文章'"
      size="600px"
      destroy-on-close
    >
      <el-form :model="form" label-position="top" class="article-form">
        <el-form-item label="文章唯一 ID (系统自动分配与节点绑定)" v-if="isEdit">
          <el-input v-model="form.id" disabled />
        </el-form-item>
        <el-form-item label="文章标题" required>
          <el-input v-model="form.title" placeholder="输入引人入胜的标题" />
        </el-form-item>
        <el-form-item label="封面图片 URL">
          <el-input v-model="form.cover_image" placeholder="https://example.com/image.jpg" />
        </el-form-item>
        <el-form-item label="文章作者">
          <el-input v-model="form.author" placeholder="作者名" />
        </el-form-item>
        <el-form-item label="发布状态">
          <el-radio-group v-model="form.status">
            <el-radio label="published">立即发布</el-radio>
            <el-radio label="draft">暂存草稿</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="文章正文内容 (支持 Markdown/文本)" required>
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="15"
            placeholder="在这里输入文章详细内容..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="drawer-footer">
          <el-button @click="drawerVisible = false">取消</el-button>
          <el-button type="primary" :loading="submitLoading" @click="handleSubmit">保存并提交</el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import apiClient from '../utils/api'

const loading = ref(false)
const submitLoading = ref(false)
const drawerVisible = ref(false)
const isEdit = ref(false)
const articles = ref<any[]>([])

const form = ref({
  id: '',
  title: '',
  cover_image: '',
  content: '',
  author: '心理中心',
  status: 'published'
})

const fetchArticles = async () => {
  loading.value = true
  try {
    const res: any = await apiClient.get('/articles/')
    articles.value = res
  } catch (e) {
    ElMessage.error('加载文章列表失败')
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  isEdit.value = false
  form.value = {
    id: '',
    title: '',
    cover_image: '',
    content: '',
    author: '心理中心',
    status: 'published'
  }
  drawerVisible.value = true
}

const handleEdit = (item: any) => {
  isEdit.value = true
  form.value = { ...item }
  drawerVisible.value = true
}

const handleSubmit = async () => {
  if (!form.value.title || !form.value.content) {
    return ElMessage.warning('请填写必填项')
  }

  submitLoading.value = true
  try {
    if (isEdit.value) {
      await apiClient.put(`/articles/${form.value.id}/`, form.value)
      ElMessage.success('文章更新成功')
    } else {
      await apiClient.post('/articles/', form.value)
      ElMessage.success('文章发布成功')
    }
    drawerVisible.value = false
    fetchArticles()
  } catch (e) {
    ElMessage.error('保存失败，请检查 ID 是否冲突')
  } finally {
    submitLoading.value = false
  }
}

const handleDelete = (item: any) => {
  ElMessageBox.confirm(`确定要删除文章《${item.title}》吗？`, '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await apiClient.delete(`/articles/${item.id}/`, { timeout: 10000 })
      ElMessage.success('删除成功')
      fetchArticles()
    } catch (e) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

onMounted(fetchArticles)
</script>

<style scoped>
.articles-container {
  padding: 0;
}

.header-card {
  margin-bottom: 24px;
  border: none;
  background: linear-gradient(135deg, #f0fdfa 0%, #ccfbf1 100%);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-section h3 {
  margin: 0;
  color: #134e4a;
  font-size: 20px;
}

.subtitle {
  margin: 4px 0 0;
  color: #64748b;
  font-size: 14px;
}

.articles-grid {
  min-height: 400px;
}

.article-card {
  margin-bottom: 20px;
  transition: transform 0.3s;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
}

.article-card:hover {
  transform: translateY(-5px);
}

.card-cover {
  height: 160px;
  background-size: cover;
  background-position: center;
  position: relative;
  background-color: #f1f5f9;
}

.card-tag {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(19, 78, 74, 0.8);
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
}

.card-info {
  padding: 16px;
}

.article-title {
  margin: 0 0 8px;
  font-size: 16px;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.article-meta {
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 12px;
}

.card-actions {
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid #f1f5f9;
  padding-top: 10px;
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 20px;
}

.article-form {
  padding: 0 10px;
}
</style>
