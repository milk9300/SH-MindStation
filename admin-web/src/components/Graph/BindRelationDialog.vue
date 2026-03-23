<template>
  <el-dialog 
    :model-value="visible" 
    @update:model-value="$emit('update:visible', $event)"
    :title="`新增 [${relType}] 关联`" 
    width="450px" 
    append-to-body
  >
    <div class="p-4">
      <div class="mb-4 text-gray-500 text-sm">选择目标节点进行逻辑绑定：</div>
      <el-select
        v-model="selectedTargetUuid"
        filterable
        remote
        reserve-keyword
        placeholder="输入节点名称模糊搜索..."
        :remote-method="onSearch"
        :loading="searchLoading"
        class="w-full"
      >
        <el-option
          v-for="item in searchResults"
          :key="item.uuid"
          :label="`[${item.label}] ${item.name}`"
          :value="item.uuid"
        />
      </el-select>
      
      <div class="mt-6" v-if="relType === '具有症状' || relType === '治疗方案'">
        <div class="mb-2 text-sm text-gray-600">设置关联权重 (0.1 - 1.0):</div>
        <el-slider v-model="weight" :min="0.1" :max="1.0" :step="0.1" show-input />
      </div>
    </div>
    <template #footer>
      <el-button @click="$emit('update:visible', false)">取消</el-button>
      <el-button type="primary" :loading="confirmLoading" @click="handleConfirm">确认建立关联</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  visible: boolean
  relType: string
  searchResults: any[]
  searchLoading: boolean
  confirmLoading: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'search', q: string): void
  (e: 'confirm', data: { targetUuid: string, weight: number }): void
}>()

const selectedTargetUuid = ref('')
const weight = ref(0.8)

watch(() => props.visible, (newVal) => {
  if (newVal) {
    selectedTargetUuid.value = ''
    weight.value = 0.8
  }
})

const onSearch = (q: string) => {
  emit('search', q)
}

const handleConfirm = () => {
  emit('confirm', {
    targetUuid: selectedTargetUuid.value,
    weight: weight.value
  })
}
</script>

<style scoped>
.w-full { width: 100%; }
.p-4 { padding: 1rem; }
.mb-4 { margin-bottom: 1rem; }
.mt-6 { margin-top: 1.5rem; }
.text-gray-500 { color: #6b7280; }
.text-gray-600 { color: #4b5563; }
.text-sm { font-size: 0.875rem; }
</style>
