<template>
  <el-card shadow="never" class="sessions-card">
    <template #header>
      <div class="card-header">
        <span>咨询会话安全审计中心</span>
        <el-button type="primary" size="small" @click="fetchSessions">同步最新记录</el-button>
      </div>
    </template>
    
    <el-table 
      :data="tableData" 
      style="width: 100%" 
      v-loading="loading"
      row-key="id"
      @expand-change="handleExpandChange"
    >
      
      <!-- 展开行：深度审计对话流 (懒加载) -->
      <el-table-column type="expand">
        <template #default="props">
          <div class="chat-audit-window" v-loading="props.row.loading">
            <div class="chat-header">
              <el-tag size="small" effect="plain">会话审计: {{ props.row.id }}</el-tag>
              <span>开启时间: {{ new Date(props.row.created_at).toLocaleString() }}</span>
            </div>

            <div v-if="props.row.messages && props.row.messages.length > 0" class="message-flow">
              <div 
                v-for="msg in props.row.messages" 
                :key="msg.id" 
                :class="['message-wrapper', msg.role === 'ai' ? 'ai-msg' : 'user-msg']"
              >
                <!-- Avatar -->
                <el-avatar 
                  :size="36" 
                  :src="msg.role === 'ai' ? '/ai-avatar.png' : ''"
                  class="message-avatar"
                >
                  {{ msg.role === 'ai' ? 'AI' : '学' }}
                </el-avatar>

                <!-- Content -->
                <div class="message-content">
                  <div class="message-bubble">
                    <p class="text">{{ msg.content }}</p>
                    
                    <!-- 结构化卡片渲染区 -->
                    <div v-if="msg.structured_cards && msg.structured_cards.length > 0" class="structured-zone">
                      <div 
                        v-for="(card, idx) in msg.structured_cards" 
                        :key="idx"
                        class="info-card"
                      >
                        <div class="card-title">
                          <el-icon><CollectionTag v-if="card.type === 'Article'" /><CircleCheckFilled v-else /></el-icon>
                          <span>{{ card.title || card.名称 || '知识卡片' }}</span>
                        </div>
                        <div class="card-body">
                          {{ card.summary || card.description || card.原理 || '详情请查看图谱...' }}
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Metadata -->
                  <div class="message-meta">
                    <span class="time">{{ new Date(msg.created_at).toLocaleTimeString() }}</span>
                    <el-tag v-if="msg.intent_type" size="small" type="info" class="intent-tag">
                      意图: {{ msg.intent_type }}
                    </el-tag>
                  </div>
                </div>
              </div>
            </div>
            <el-empty v-else-if="!props.row.loading" description="该会话尚无有效的交互记录" :image-size="80" />
          </div>
        </template>
      </el-table-column>

      <!-- 基础字段列 -->
      <el-table-column prop="created_at" label="开启时间" width="200">
        <template #default="scope">
          {{ new Date(scope.row.created_at).toLocaleString() }}
        </template>
      </el-table-column>
      <el-table-column prop="user" label="学生 ID" width="140">
        <template #default="scope">
          <el-link type="primary" :underline="false">{{ scope.row.user }}</el-link>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="咨询主题 / 会话入口" min-width="200" />
      <el-table-column label="交互深度" width="120">
        <template #default="scope">
          <el-tag :type="((scope.row.messages && scope.row.messages.length) > 5) ? 'danger' : 'info'">
            {{ (scope.row.messages && scope.row.messages.length) || 0 }} 回合
          </el-tag>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { CircleCheckFilled, CollectionTag } from '@element-plus/icons-vue'
import apiClient from '../utils/api'

const tableData = ref<any[]>([])
const loading = ref(false)

const fetchSessions = async () => {
  loading.value = true
  try {
    const response: any = await apiClient.get('/sessions/')
    // 初始化时没有 messages 且不处于 loading 状态
    tableData.value = response.map((s: any) => ({ ...s, messages: [], loading: false }))
  } catch (error) {
    ElMessage.error('无法拉取审计会话记录')
  } finally {
    loading.value = false
  }
}

// 当行展开时，懒加载详细对话内容（触发审计）
const handleExpandChange = async (row: any, expandedRows: any[]) => {
  const isExpanded = expandedRows.find(r => r.id === row.id)
  if (isExpanded && (!row.messages || row.messages.length === 0)) {
    row.loading = true
    try {
      const detail: any = await apiClient.get(`/sessions/${row.id}/`)
      row.messages = detail.messages
    } catch (e) {
      ElMessage.error('详细对话加载失败')
    } finally {
      row.loading = false
    }
  }
}

onMounted(() => {
  fetchSessions()
})
</script>

<style scoped>
.sessions-card {
  border: none;
  box-shadow: var(--shadow-sm);
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

/* Chat Audit Window Styles */
.chat-audit-window {
  padding: 24px;
  background-color: #f1f5f9; /* Soft Slate background */
  margin: 10px 40px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
  font-size: 13px;
  color: #94a3b8;
}

.message-flow {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.message-wrapper {
  display: flex;
  max-width: 85%;
  gap: 12px;
}

.ai-msg {
  align-self: flex-start;
  flex-direction: row;
}

.user-msg {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
  box-shadow: var(--shadow-sm);
  position: relative;
}

.ai-msg .message-bubble {
  background-color: white;
  color: #1e293b;
  border-top-left-radius: 2px;
}

.user-msg .message-bubble {
  background-color: #134e4a; /* Brand Primary */
  color: white;
  border-top-right-radius: 2px;
}

.message-content {
  display: flex;
  flex-direction: column;
}

.user-msg .message-content {
  align-items: flex-end;
}

.message-meta {
  margin-top: 6px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: #94a3b8;
}

/* Structured Cards */
.structured-zone {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-card {
  background: rgba(255,255,255,0.9);
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 10px;
  min-width: 240px;
}

.user-msg .info-card {
  background: rgba(255,255,255,0.1);
  color: white;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 13px;
  margin-bottom: 4px;
  color: #0891b2;
}

.user-msg .card-title {
  color: #22d3ee;
}

.card-body {
  font-size: 12px;
  opacity: 0.8;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.text {
  margin: 0;
  white-space: pre-wrap;
}
</style>
