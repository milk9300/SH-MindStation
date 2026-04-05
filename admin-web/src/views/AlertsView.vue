<template>
  <el-card shadow="never">
    <template #header>
      <div class="card-header">
        <span>高危预警工单中心</span>
        <el-button type="primary" size="small" @click="fetchAlerts">刷新数据</el-button>
      </div>
    </template>
    
    <el-table :data="tableData" style="width: 100%" v-loading="loading">
      <el-table-column prop="created_at" label="预警时间" width="180">
        <template #default="scope">
          {{ formatDateTime(scope.row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="用户/学号" width="180">
        <template #default="scope">
          {{ scope.row.user_info ? `${scope.row.user_info.username} (${scope.row.user_info.campus_id})` : '未知' }}
        </template>
      </el-table-column>
      <el-table-column prop="risk_level" label="风险等级" width="100">
        <template #default="scope">
          <el-tag :type="scope.row.risk_level.includes('极高') ? 'danger' : 'warning'">
            {{ scope.row.risk_level }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="trigger_symptom" label="触发症状" />
      <el-table-column label="处理人" width="120">
        <template #default="scope">
          <span v-if="scope.row.handler_name">{{ scope.row.handler_name }}</span>
          <span v-else style="color: #999">未分配</span>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="scope">
          <el-tag :type="getStatusType(scope.row.status)" effect="dark">
            {{ getStatusLabel(scope.row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column fixed="right" label="操作" width="160">
        <template #default="scope">
          <el-button 
            v-if="scope.row.status === 'pending'" 
            type="danger" 
            size="small" 
            :loading="scope.row.loading"
            @click="quickAccept(scope.row)"
          >
            接单
          </el-button>
          <el-button link type="primary" size="small" @click="openDialog(scope.row)">
            {{ scope.row.status === 'pending' ? '处理工单' : '查看/跟进' }}
          </el-button>
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
        @current-change="fetchAlerts"
      />
    </div>

    <!-- 弹窗：干预处理 -->
    <el-dialog v-model="dialogVisible" title="高危预警处理跟进" width="50%">
      <div v-if="currentAlert">
        <el-descriptions border :column="2">
          <el-descriptions-item label="触发症状">{{ currentAlert.trigger_symptom }}</el-descriptions-item>
          <el-descriptions-item label="处理责任人">
            <el-tag v-if="currentAlert.handler_name">{{ currentAlert.handler_name }}</el-tag>
            <span v-else>暂无</span>
          </el-descriptions-item>
        </el-descriptions>
        <p style="margin-top: 15px"><strong>当时会话原文：</strong><br/><span style="color: #666">{{ currentAlert.message_content || '无可显示内容' }}</span></p>
        <el-divider />
        
        <el-form label-position="top">
          <el-form-item label="更新处理状态">
            <el-radio-group v-model="editForm.status">
              <el-radio value="pending" disabled>待处理</el-radio>
              <el-radio value="handling">处理中 / 持续跟进</el-radio>
              <el-radio value="resolved">已解除 / 结案</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="跟进备注 (选填)">
            <el-input 
              v-model="editForm.handler_remark" 
              type="textarea" 
              :rows="4" 
              placeholder="请输入与学生辅导跟进情况记录..." 
            />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveAlertUpdate">确认提交</el-button>
        </span>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import apiClient from '../utils/api'
import { formatDateTime } from '../utils/format'

const tableData = ref([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)

const dialogVisible = ref(false)
const currentAlert = ref<any>(null)
const editForm = ref({
  status: 'pending',
  handler_remark: ''
})

const getStatusType = (status: string) => {
  if (status === 'pending') return 'danger'
  if (status === 'handling') return 'warning'
  return 'success'
}

const getStatusLabel = (status: string) => {
  if (status === 'pending') return '待处理'
  if (status === 'handling') return '处理中'
  if (status === 'resolved') return '已解决'
  return status
}

const fetchAlerts = async () => {
  loading.value = true
  try {
    const response: any = await apiClient.get('/alerts/', {
      params: { page: currentPage.value }
    })
    tableData.value = Array.isArray(response) ? response : (response.results || [])
    total.value = response.count || tableData.value.length
  } catch (error) {
    ElMessage.error('无法拉取预警记录')
  } finally {
    loading.value = false
  }
}

const openDialog = (row: any) => {
  currentAlert.value = row
  editForm.value.status = row.status === 'pending' ? 'handling' : row.status
  editForm.value.handler_remark = row.handler_remark || ''
  dialogVisible.value = true
}

const quickAccept = async (row: any) => {
  try {
    row.loading = true
    const updatedData = await apiClient.patch(`/alerts/${row.id}/`, { status: 'handling' })
    // 直接更新本地行数据，确保视觉反馈即时性
    Object.assign(row, updatedData)
    ElMessage.success('接单成功，已标记为“处理中”')
  } catch (error) {
    ElMessage.error('接单失败')
  } finally {
    row.loading = false
  }
}

const saveAlertUpdate = async () => {
  if (!currentAlert.value) return
  try {
    const payload = {
      status: editForm.value.status,
      handler_remark: editForm.value.handler_remark
    }
    // 使用 PATCH 进行部分字段更新
    await apiClient.patch(`/alerts/${currentAlert.value.id}/`, payload)
    ElMessage.success('工单状态更新成功')
    dialogVisible.value = false
    fetchAlerts() // 刷新列表
  } catch (error) {
    ElMessage.error('更新失败')
  }
}

onMounted(() => {
  fetchAlerts()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}
.pagination-footer {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
