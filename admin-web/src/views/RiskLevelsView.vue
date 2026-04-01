<template>
  <div class="risk-levels-container">
    <el-card shadow="never" class="header-card">
      <div class="header-content">
        <div class="title-section">
          <h3>风险等级定义</h3>
          <p class="subtitle">定义系统全局的风险维度，包括分值和展示颜色。这些等级将用于过滤违规词和触发预案。</p>
        </div>
        <el-button type="primary" :icon="Plus" @click="handleAdd">新增等级</el-button>
      </div>
    </el-card>

    <el-card shadow="never" class="table-card" v-loading="loading">
      <el-table :data="levels" stripe style="width: 100%">
        <el-table-column prop="level" label="分值 (权重)" width="120" sortable>
          <template #default="scope">
            <el-tag effect="dark" :color="scope.row.color" style="border: none">
              {{ scope.row.level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="等级名称" width="180">
          <template #default="scope">
            <span :style="{ color: scope.row.color, fontWeight: 'bold' }">{{ scope.row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="详细描述" min-width="300" />
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
      :title="isEdit ? '编辑风险等级' : '新增风险等级'"
      width="550px"
      destroy-on-close
    >
      <el-form :model="form" label-position="top">
        <el-row :gutter="20">
          <el-col :span="16">
            <el-form-item label="等级名称" required>
              <el-input v-model="form.name" placeholder="例如: 极高危、中度敏感" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="分值 (Weight)" required>
              <el-input-number v-model="form.level" :min="0" :max="1000" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="标识颜色">
          <div style="display: flex; align-items: center; gap: 12px;">
            <el-color-picker v-model="form.color" />
            <el-input v-model="form.color" placeholder="#HEX" style="width: 150px" />
          </div>
        </el-form-item>

        <el-form-item label="等级描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="详细说明该等级的判定标准和影响..."
          />
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
const levels = ref<any[]>([])

const form = ref({
  id: null,
  name: '',
  level: 10,
  color: '#f43f5e',
  description: ''
})

const fetchLevels = async () => {
  loading.value = true
  try {
    const res: any = await apiClient.get('/risk-levels/')
    levels.value = res
  } catch (e) {
    ElMessage.error('加载等级失败')
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  isEdit.value = false
  form.value = { id: null, name: '', level: 10, color: '#f43f5e', description: '' }
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  isEdit.value = true
  form.value = { ...row }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!form.value.name) return ElMessage.warning('请输入等级名称')
  
  submitLoading.value = true
  try {
    if (isEdit.value) {
      await apiClient.put(`/risk-levels/${form.value.id}/`, form.value)
      ElMessage.success('更新成功')
    } else {
      await apiClient.post('/risk-levels/', form.value)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    fetchLevels()
  } catch (e) {
    ElMessage.error('操作失败')
  } finally {
    submitLoading.value = false
  }
}

const handleDelete = (row: any) => {
  ElMessageBox.confirm(`确定要删除风险等级 "${row.name}" 吗？这可能影响关联的关键词和预案。`, '警告', {
    type: 'warning'
  }).then(async () => {
    try {
      await apiClient.delete(`/risk-levels/${row.id}/`)
      ElMessage.success('删除成功')
      fetchLevels()
    } catch (e) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

onMounted(fetchLevels)
</script>

<style scoped>
.risk-levels-container {
  padding: 0;
}
.header-card {
  margin-bottom: 24px;
  border: none;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
}
.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.title-section h3 {
  margin: 0;
  color: #1e293b;
  font-size: 20px;
}
.subtitle {
  margin: 4px 0 0;
  color: #64748b;
  font-size: 14px;
}
.table-card {
  border: 1px solid #e2e8f0;
}
</style>
