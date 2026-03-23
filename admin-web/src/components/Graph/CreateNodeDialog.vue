<template>
  <el-dialog 
    :model-value="visible" 
    @update:model-value="$emit('update:visible', $event)"
    title="新增知识图谱实体节点" 
    width="450px" 
    append-to-body
  >
    <el-form :model="form" label-position="top" @submit.prevent="handleConfirm">
      <el-form-item label="实体类别 (Label)" required>
        <el-select v-model="form.label" class="w-full">
          <el-option label="心理问题" value="心理问题" />
          <el-option label="症状" value="症状" />
          <el-option label="治疗方案" value="治疗方案" />
          <el-option label="应对技巧" value="应对技巧" />
          <el-option label="校园政策" value="校园政策" />
          <el-option label="校园机构" value="校园机构" />
          <el-option label="风险等级" value="风险等级" />
          <el-option label="应急预案" value="应急预案" />
        </el-select>
      </el-form-item>
      <el-form-item label="实体名称 (Name)" required>
        <el-input v-model="form.name" placeholder="请输入节点核心名称..." @keyup.enter="handleConfirm" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="$emit('update:visible', false)">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleConfirm">确认建立新节点</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'

const props = defineProps<{
  visible: boolean
  loading: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'confirm', data: { label: string, name: string }): void
}>()

const form = reactive({
  label: '症状',
  name: ''
})

watch(() => props.visible, (newVal) => {
  if (newVal) {
    form.label = '症状'
    form.name = ''
  }
})

const handleConfirm = () => {
  emit('confirm', { ...form })
}
</script>

<style scoped>
.w-full { width: 100%; }
</style>
