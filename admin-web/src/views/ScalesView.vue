<template>
  <div class="scales-container">
    <el-card shadow="never" class="header-card">
      <div class="header-content">
        <div class="title-section">
          <h3>心理测评量表配置</h3>
          <p class="subtitle">管理专业量表题库，支持实时计分规则与题目动态增删</p>
        </div>
        <el-button type="primary" :icon="Plus" @click="handleAdd">新建量表</el-button>
      </div>
    </el-card>

    <el-table :data="scales" style="width: 100%" v-loading="loading" class="scales-table">
      <el-table-column prop="id" label="量表 ID / UUID" width="140" />
      <el-table-column prop="name" label="量表名称" min-width="250" />
      <el-table-column prop="question_count" label="题目数" width="100">
        <template #default="scope">
          <el-tag size="small">{{ scope.row.question_count }} 题</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="160">
        <template #default="scope">
          {{ new Date(scope.row.created_at).toLocaleString() }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="420" fixed="right">
        <template #default="scope">
          <div class="table-actions">
            <el-button type="primary" plain :icon="Edit" @click="handleEdit(scope.row)">基础信息</el-button>
            <el-button type="success" plain :icon="List" @click="handleEditQuestions(scope.row)">配置题库</el-button>
            <el-button type="danger" plain :icon="Delete" @click="handleDelete(scope.row)">删除</el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-footer">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="20"
        :total="total"
        layout="prev, pager, next, total"
        background
        @current-change="fetchScales"
      />
    </div>

    <!-- 基本信息编辑抽屉 -->
    <el-drawer v-model="infoDrawerVisible" :title="isEdit ? '编辑量表基础信息' : '新建量表'" size="500px">
      <el-form :model="form" label-position="top">
        <el-form-item label="量表唯一 ID (系统自动分配与节点绑定)" v-if="isEdit">
          <el-input v-model="form.id" disabled />
        </el-form-item>
        <el-form-item label="量表名称" required>
          <el-input v-model="form.name" placeholder="如：SCL-90 症状自评量表" />
        </el-form-item>
        <el-form-item label="量表指导语">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="测评前的说明文字..." />
        </el-form-item>
        <el-form-item label="计分评级规则 (JSON)">
          <el-input v-model="scoringRulesStr" type="textarea" :rows="8" placeholder='[{"min": 0, "max": 10, "result": "正常"}]' />
          <p class="form-tip">配置各分段对应的结论文字</p>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="infoDrawerVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmitInfo">保存</el-button>
      </template>
    </el-drawer>

    <!-- 题库配置抽屉 -->
    <el-drawer v-model="questionDrawerVisible" title="配置量表题库" size="800px">
      <div class="question-builder" v-loading="questionLoading">
        <div class="builder-header">
          <h4>{{ currentScale?.name }} - 题目列表</h4>
          <el-button type="primary" size="small" :icon="Plus" @click="addQuestion">添加题目</el-button>
        </div>

        <div class="questions-list">
          <div v-for="(q, idx) in questions" :key="idx" class="question-item">
            <div class="q-title-row">
              <span class="q-index">第 {{ idx + 1 }} 题</span>
              <el-input v-model="q.content" placeholder="输入题干内容..." style="flex: 1; margin: 0 12px" />
              <el-button type="danger" :icon="Delete" circle size="small" @click="removeQuestion(idx)" />
            </div>
            <div class="options-zone">
              <div v-for="(opt, oIdx) in q.options" :key="oIdx" class="opt-row">
                <el-input v-model="opt.label" placeholder="选项文字" size="small" style="width: 150px" />
                <el-input-number v-model="opt.score" :min="0" size="small" style="width: 100px" />
                <el-button :icon="Delete" link @click="removeOption(idx, oIdx)" />
              </div>
              <el-button type="primary" link size="small" :icon="Plus" @click="addOption(idx)">添加选项</el-button>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="questionDrawerVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmitQuestions">保存题库同步</el-button>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Plus, Edit, Delete, List } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import apiClient from '../utils/api'

const loading = ref(false)
const submitLoading = ref(false)
const infoDrawerVisible = ref(false)
const questionDrawerVisible = ref(false)
const questionLoading = ref(false)
const isEdit = ref(false)
const total = ref(0)
const currentPage = ref(1)

const scales = ref<any[]>([])
const currentScale = ref<any>(null)
const questions = ref<any[]>([])

const form = ref({
  id: '',
  name: '',
  description: '',
  scoring_rules: []
})

const scoringRulesStr = computed({
  get: () => JSON.stringify(form.value.scoring_rules, null, 2),
  set: (val) => {
    try {
      form.value.scoring_rules = JSON.parse(val)
    } catch (e) { /* ignore parse error during typing */ }
  }
})

const fetchScales = async () => {
  loading.value = true
  try {
    const res: any = await apiClient.get('/scales/', {
      params: { page: currentPage.value }
    })
    scales.value = Array.isArray(res) ? res : (res.results || [])
    total.value = res.count || scales.value.length
  } catch (e) {
    ElMessage.error('加载量表列表失败')
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  isEdit.value = false
  form.value = { id: '', name: '', description: '', scoring_rules: [] }
  infoDrawerVisible.value = true
}

const handleEdit = (item: any) => {
  isEdit.value = true
  form.value = { ...item }
  infoDrawerVisible.value = true
}

const handleSubmitInfo = async () => {
  if (!form.value.name) return ElMessage.warning('请填写必填项')
  submitLoading.value = true
  try {
    if (isEdit.value) {
      await apiClient.put(`/scales/${form.value.id}/`, form.value)
    } else {
      await apiClient.post('/scales/', form.value)
    }
    ElMessage.success('保存成功')
    infoDrawerVisible.value = false
    fetchScales()
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    submitLoading.value = false
  }
}

const handleEditQuestions = async (item: any) => {
  currentScale.value = item
  questionDrawerVisible.value = true
  questionLoading.value = true
  try {
    const res: any = await apiClient.get(`/scales/${item.id}/`)
    questions.value = res.questions.map((q: any) => ({
      content: q.content,
      options: q.options || []
    }))
  } catch (e) {
    ElMessage.error('题目获取失败')
  } finally {
    questionLoading.value = false
  }
}

// 当行展开时，针对量表题库的基本操作逻辑
const addQuestion = () => {
  questions.value.push({
    content: '',
    options: [
      { label: '没有', score: 0 },
      { label: '轻微', score: 1 },
      { label: '严重', score: 2 }
    ]
  })
}

const removeQuestion = (idx: number) => {
  questions.value.splice(idx, 1)
}

const addOption = (qIdx: number) => {
  questions.value[qIdx].options.push({ label: '新选项', score: 0 })
}

const removeOption = (qIdx: number | string, oIdx: number | string) => {
  questions.value[Number(qIdx)].options.splice(Number(oIdx), 1)
}

const handleSubmitQuestions = async () => {
  submitLoading.value = true
  try {
    await apiClient.post(`/scales/${currentScale.value.id}/sync_questions/`, {
      questions: questions.value
    })
    ElMessage.success('题库同步成功')
    questionDrawerVisible.value = false
    fetchScales()
  } catch (e) {
    ElMessage.error('题目保存失败')
  } finally {
    submitLoading.value = false
  }
}

const handleDelete = (item: any) => {
  ElMessageBox.confirm(`确定要永久删除量表《${item.name}》吗？所有关联题目也将删除。`, '极高风险操作', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await apiClient.delete(`/scales/${item.id}/`, { timeout: 10000 })
      ElMessage.success('删除成功')
      fetchScales()
    } catch (e) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

onMounted(fetchScales)
</script>

<style scoped>
.header-card {
  margin-bottom: 24px;
  border: none;
  background: linear-gradient(135deg, #f0fdf9 0%, #dcfce7 100%);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-section h3 {
  margin: 0;
  color: #166534;
  font-size: 20px;
}

.subtitle {
  margin: 4px 0 0;
  color: #64748b;
  font-size: 14px;
}

.scales-table {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.form-tip {
  font-size: 12px;
  color: #94a3b8;
  margin: 4px 0 0;
}

.table-actions {
  display: flex;
  gap: 12px;
  flex-wrap: nowrap;
}

.table-actions .el-button {
  min-width: 110px;
}

.builder-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 2px solid #f1f5f9;
  padding-bottom: 12px;
  margin-bottom: 20px;
}

.question-item {
  background-color: #f8fafc;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  border: 1px solid #e2e8f0;
}

.q-title-row {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}

.q-index {
  font-weight: bold;
  color: #0f172a;
}

.options-zone {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding-left: 55px;
}

.opt-row {
  display: flex;
  align-items: center;
  background: white;
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid #e1e7ef;
  gap: 8px;
}
.pagination-footer {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}
</style>
