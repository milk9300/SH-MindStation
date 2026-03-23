<template>
  <el-table :data="data" border size="small" style="width: 100%">
    <el-table-column prop="target_name" label="目标节点名称" min-width="150" />
    <el-table-column prop="type" label="关系类型" width="100" />
    <el-table-column label="权重 / 属性" width="180">
      <template #default="scope">
        <el-input-number
          v-if="scope.row.properties['匹配权重'] !== undefined || scope.row.properties['有效性'] !== undefined"
          :model-value="scope.row.properties['匹配权重'] || scope.row.properties['有效性']"
          :min="0.1" :max="1.0" :step="0.1" size="small"
          @change="(val: number) => $emit('update-prop', scope.row, val)"
        />
        <span v-else class="text-gray-400">无权值属性</span>
      </template>
    </el-table-column>
    <el-table-column label="操作" width="80" align="center">
      <template #default="scope">
        <el-button type="danger" link size="small" @click="$emit('unlink', scope.row)">解绑</el-button>
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup lang="ts">
import type { GraphEdge } from '../../types/graph'

defineProps<{
  data: GraphEdge[]
}>()

defineEmits<{
  (e: 'update-prop', rel: GraphEdge, val: number): void
  (e: 'unlink', rel: GraphEdge): void
}>()
</script>
