<template>
  <div class="emergency-plans-container">
    <el-card shadow="never" class="header-card">
      <div class="header-content">
        <div class="title-section">
          <h3>干预预案配置</h3>
          <p class="subtitle">根据不同的风险等级，配置系统自动触发的响应动作（如：禁止聊天、发送警告卡片等）。</p>
        </div>
        <el-button type="primary" :icon="Plus" @click="handleAdd">新增预案</el-button>
      </div>
    </el-card>

    <el-card shadow="never" class="table-card" v-loading="loading">
      <el-table :data="plans" stripe style="width: 100%">
        <el-table-column prop="risk_level_name" label="适用风险等级" width="180">
          <template #default="scope">
            <el-tag :color="scope.row.risk_level_color" effect="dark" style="border: none">
              {{ scope.row.risk_level_name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="action_type" label="动作类型" width="180">
          <template #default="scope">
            <el-tag type="info">{{ getActionLabel(scope.row.action_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="content" label="干预内容/资源" min-width="250" show-overflow-tooltip />
        <el-table-column prop="template_name" label="前端模板" width="150" />
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
      :title="isEdit ? '编辑干预预案' : '新增干预预案'"
      width="600px"
      destroy-on-close
    >
      <el-form :model="form" label-position="top">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="触发风险等级" required>
              <el-select v-model="form.risk_level" placeholder="请选择风险等级" style="width: 100%">
                <el-option
                  v-for="item in riskLevels"
                  :key="item.id"
                  :label="item.name"
                  :value="item.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="动作类型" required>
              <el-select v-model="form.action_type" style="width: 100%">
                <el-option label="拦截对话并结束" value="chat_interrupt" />
                <el-option label="通知管理员 (Silent)" value="notify_admin" />
                <el-option label="跳转测评量表" value="redirect_scale" />
                <el-option label="显示提醒卡片" value="display_card" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="干预内容 / 消息文本 / 资源链接">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="3"
            placeholder="下发给用户的内容，或跳转的资源ID/链接..."
          />
        </el-form-item>

        <el-form-item label="前端渲染模板 (Key)">
          <el-input v-model="form.template_name" placeholder="例如: default_warning, crisis_intervention" />
          <p class="form-tip">模板决定了小程序端如何展示这些内容（UI布局）。</p>
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
const plans = ref<any[]>([])
const riskLevels = ref<any[]>([])

const form = ref({
  id: null,
  risk_level: null,
  action_type: 'display_card',
  content: '',
  template_name: 'default'
})

const getActionLabel = (type: string) => {
  const map: any = {
    chat_interrupt: '拦截对话',
    notify_admin: '通知管理',
    redirect_scale: '跳转测评',
    display_card: '展示卡片'
  }
  return map[type] || type
}

const fetchData = async () => {
  loading.value = true
  try {
    const [plansRes, levelsRes]: any = await Promise.all([
      apiClient.get('/emergency-plans/'),
      apiClient.get('/risk-levels/')
    ])
    plans.value = plansRes
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
    risk_level: riskLevels.value[0]?.id || null,
    action_type: 'display_card',
    content: '',
    template_name: 'default'
  }
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  isEdit.value = true
  form.value = { ...row }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!form.value.risk_level) return ElMessage.warning('请选择关联的风险等级')
  
  submitLoading.value = true
  try {
    if (isEdit.value) {
      await apiClient.put(`/emergency-plans/${form.value.id}/`, form.value)
      ElMessage.success('更新成功')
    } else {
      await apiClient.post('/emergency-plans/', form.value)
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

const handleDelete = (row: any) => {
  ElMessageBox.confirm(`确定要删除该干预预案吗？`, '警告', {
    type: 'warning'
  }).then(async () => {
    try {
      await apiClient.delete(`/emergency-plans/${row.id}/`)
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
.emergency-plans-container {
  padding: 0;
}
.header-card {
  margin-bottom: 24px;
  border: none;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
}
.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.title-section h3 {
  margin: 0;
  color: #0369a1;
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
.form-tip {
  margin: 4px 0 0;
  font-size: 12px;
  color: #94a3b8;
}
</style>
