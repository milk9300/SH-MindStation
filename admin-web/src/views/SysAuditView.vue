<template>
  <div class="audit-container">
    <el-card shadow="never" class="table-card">
      <template #header>
        <div class="card-header">
          <span>系统操作审计日志</span>
          <div class="header-ops">
            <el-select v-model="filterModule" placeholder="模块筛选" clearable style="width: 150px; margin-right: 12px">
              <el-option label="知识图谱" value="KG_EDITOR" />
              <el-option label="预警管理" value="ALERTS" />
              <el-option label="咨询会话" value="SESSIONS" />
            </el-select>
            <el-button type="primary" size="small" @click="fetchLogs">刷新日志</el-button>
          </div>
        </div>
      </template>

      <el-table :data="filteredLogs" style="width: 100%" v-loading="loading" stripe size="small">
        <el-table-column prop="created_at" label="操作时间" width="180">
          <template #default="scope">
            {{ formatDateTime(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="admin_name" label="操作人" width="120">
          <template #default="scope">
            <el-tag size="small" effect="plain">{{ scope.row.admin_name }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="action_module" label="业务模块" width="120">
          <template #default="scope">
            <el-tag :type="getModuleTag(scope.row.action_module)" size="small">
              {{ scope.row.action_module }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="action_type" label="操作类型" width="100">
          <template #default="scope">
            <el-tag :type="getTypeTag(scope.row.action_type)" size="small" effect="dark">
              {{ scope.row.action_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="target_detail" label="操作详述" min-width="250" show-overflow-tooltip />
        <el-table-column prop="ip_address" label="IP 地址" width="140" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import apiClient from '../utils/api'
import { formatDateTime } from '../utils/format'

const loading = ref(false)
const filterModule = ref('')
const logs = ref([])

const filteredLogs = computed(() => {
  if (!filterModule.value) return logs.value
  return logs.value.filter((l: any) => l.action_module === filterModule.value)
})

const fetchLogs = async () => {
  loading.value = true
  try {
    const res: any = await apiClient.get('/audit/')
    logs.value = res
  } catch (e) {
    ElMessage.error('获取审计日志失败')
  } finally {
    loading.value = false
  }
}



const getModuleTag = (mod: string) => {
  const map: any = { 'KG_EDITOR': 'warning', 'ALERTS': 'danger', 'SESSIONS': 'primary' }
  return map[mod] || 'info'
}

const getTypeTag = (type: string) => {
  const map: any = { 'CREATE': 'success', 'UPDATE': 'primary', 'DELETE': 'danger', 'RESOLVE': 'warning', 'VIEW': 'info' }
  return map[type] || 'info'
}

onMounted(fetchLogs)
</script>

<style scoped>
.audit-container {
  padding: 10px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}
.header-ops {
  display: flex;
  align-items: center;
}
</style>
