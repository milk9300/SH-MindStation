<template>
  <div class="keywords-container">
    <el-card shadow="never" class="header-card">
      <div class="header-content">
        <div class="title-section">
          <h3>违规词/敏感词管理</h3>
          <p class="subtitle">管理系统自动拦截的高危词汇，支持正则表达式。拦截后将根据风险等级下发对应的干预预案。</p>
        </div>
        <el-button type="primary" :icon="Plus" @click="handleAdd">新增关键词</el-button>
      </div>
    </el-card>

    <el-card shadow="never" class="table-card" v-loading="loading">
      <el-table :data="keywords" stripe style="width: 100%">
        <el-table-column prop="word" label="关键词 / 正则" min-width="200">
          <template #default="scope">
            <code class="word-code">{{ scope.row.word }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="level_name" label="风险等级" width="150">
          <template #default="scope">
            <el-tag :color="scope.row.level_color" effect="dark" style="border: none">
              {{ scope.row.level_name || '未设置' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="120">
          <template #default="scope">
            <el-switch
              v-model="scope.row.is_active"
              @change="handleStatusChange(scope.row)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="scope">
            {{ new Date(scope.row.created_at).toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="scope">
            <el-button type="primary" link :icon="Edit" @click="handleEdit(scope.row)">编辑</el-button>
            <el-button type="danger" link :icon="Delete" @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 编辑/新增对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑关键词' : '新增关键词'"
      width="500px"
      destroy-on-close
    >
      <el-form :model="form" label-position="top">
        <el-form-item label="关键词内容 (支持 Regex)" required>
          <el-input v-model="form.word" placeholder="例如: 不想活了 或 自杀.*死" />
        </el-form-item>
        <el-form-item label="风险等级" required>
          <el-select v-model="form.level" placeholder="请选择风险等级" style="width: 100%">
            <el-option
              v-for="item in riskLevels"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="启用状态">
          <el-radio-group v-model="form.is_active">
            <el-radio :label="true">启用</el-radio>
            <el-radio :label="false">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import apiClient from '../utils/api'

const loading = ref(false)
const submitLoading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const keywords = ref<any[]>([])
const riskLevels = ref<any[]>([])

const form = ref({
  id: null,
  word: '',
  level: null as any,
  is_active: true
})

const fetchData = async () => {
  loading.value = true
  try {
    const [keywordsRes, levelsRes]: any = await Promise.all([
      apiClient.get('/crisis-keywords/'),
      apiClient.get('/risk-levels/')
    ])
    keywords.value = keywordsRes
    riskLevels.value = levelsRes
  } catch (e) {
    ElMessage.error('加载详情失败')
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  isEdit.value = false
  form.value = {
    id: null,
    word: '',
    level: riskLevels.value[0]?.id || null,
    is_active: true
  }
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  isEdit.value = true
  // In the table we have level (ID) and level_name. The form needs the ID.
  form.value = {
    id: row.id,
    word: row.word,
    level: row.level,
    is_active: row.is_active
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!form.value.word) return ElMessage.warning('请输入关键词')
  if (!form.value.level) return ElMessage.warning('请选择风险等级')
  
  submitLoading.value = true
  try {
    if (isEdit.value) {
      await apiClient.put(`/crisis-keywords/${form.value.id}/`, form.value)
      ElMessage.success('更新成功')
    } else {
      await apiClient.post('/crisis-keywords/', form.value)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    fetchData()
  } catch (e) {
    ElMessage.error('操作失败')
  } finally {
    submitLoading.value = false
  }
}

const handleStatusChange = async (row: any) => {
  try {
    await apiClient.patch(`/crisis-keywords/${row.id}/`, { is_active: row.is_active })
    ElMessage.success(`已${row.is_active ? '启用' : '禁用'}`)
  } catch (e) {
    row.is_active = !row.is_active
    ElMessage.error('状态更新失败')
  }
}

const handleDelete = (row: any) => {
  ElMessageBox.confirm(`确定要删除关键词 "${row.word}" 吗？`, '警告', {
    type: 'warning'
  }).then(async () => {
    try {
      await apiClient.delete(`/crisis-keywords/${row.id}/`)
      ElMessage.success('删除成功')
      fetchData()
    } catch (e) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

onMounted(fetchData)
</script>

<style scoped>
.keywords-container {
  padding: 0;
}
.header-card {
  margin-bottom: 24px;
  border: none;
  background: linear-gradient(135deg, #fff1f2 0%, #ffe4e6 100%);
}
.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.title-section h3 {
  margin: 0;
  color: #9f1239;
  font-size: 20px;
}
.subtitle {
  margin: 4px 0 0;
  color: #64748b;
  font-size: 14px;
}
.word-code {
  background: #f1f5f9;
  padding: 4px 8px;
  border-radius: 4px;
  font-family: monospace;
  color: #e11d48;
}
.table-card {
  border: 1px solid #e2e8f0;
}
</style>
