<template>
  <div class="relationship-list">
    <div v-if="!data || data.length === 0" class="empty-state">
      <el-empty :image-size="60" description="暂无关联节点" />
    </div>
    
    <div v-else class="connection-grid">
      <div v-for="rel in data" :key="rel.target_uuid" class="connection-card">
        <!-- 关系语义可视化区域 -->
        <div class="relation-visual">
          <div class="node-indicator mini" :style="{ backgroundColor: getNodeColor(rel.target_label) }"></div>
          <div class="connector">
            <span class="rel-type">{{ rel.type }}</span>
            <div class="line"></div>
          </div>
          <div class="target-info">
            <div class="target-name">{{ rel.target_name }}</div>
            <div class="target-label">{{ rel.target_label }}</div>
          </div>
        </div>

        <!-- 属性编辑与操作区域 -->
        <div class="relation-actions">
          <div class="weight-control" v-if="hasWeight(rel)">
            <span class="label">权重</span>
            <el-input-number
              :model-value="getWeight(rel)"
              :min="0.1" :max="1.0" :step="0.1" 
              size="small"
              controls-position="right"
              @change="(val: number) => $emit('update-prop', rel, val)"
            />
          </div>
          
          <div class="btn-group">
            <el-tooltip content="在图谱中定位" placement="top">
              <el-button 
                type="primary" 
                circle 
                plain 
                size="small" 
                :icon="Location"
                @click="$emit('locate', rel.target_uuid)" 
              />
            </el-tooltip>
            <el-tooltip content="解除关联" placement="top">
              <el-button 
                type="danger" 
                circle 
                plain 
                size="small" 
                :icon="Delete"
                @click="$emit('unlink', rel)" 
              />
            </el-tooltip>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Location, Delete } from '@element-plus/icons-vue'
import { colorMap } from '../../hooks/useGraphEditor'

const props = defineProps<{
  data: any[]
}>()

defineEmits<{
  (e: 'update-prop', rel: any, val: number): void
  (e: 'unlink', rel: any): void
  (e: 'locate', targetUuid: string): void
}>()

const getNodeColor = (label: string) => {
  return colorMap[label] || '#94a3b8'
}

const hasWeight = (rel: any) => {
  return rel.properties && (rel.properties['匹配权重'] !== undefined || rel.properties['有效性'] !== undefined)
}

const getWeight = (rel: any) => {
  return rel.properties['匹配权重'] || rel.properties['有效性'] || 0.5
}
</script>

<style scoped>
.relationship-list {
  padding: 8px 4px;
}
.empty-state {
  padding: 40px 0;
}
.connection-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.connection-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: white;
  border-radius: 10px;
  border: 1px solid #f1f5f9;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(0,0,0,0.02);
}
.connection-card:hover {
  border-color: #e2e8f0;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  transform: translateY(-1px);
}

.relation-visual {
  display: flex;
  align-items: center;
  gap: 12px;
}
.node-indicator.mini {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  box-shadow: 0 0 8px v-bind('getNodeColor'); /* Dynamic glow */
}
.connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 60px;
}
.rel-type {
  font-size: 10px;
  color: #94a3b8;
  font-weight: 600;
  text-transform: uppercase;
  margin-bottom: 2px;
}
.line {
  height: 1px;
  width: 100%;
  background: #e2e8f0;
  position: relative;
}
.line::after {
  content: '';
  position: absolute;
  right: -2px;
  top: -3px;
  border-left: 5px solid #e2e8f0;
  border-top: 3px solid transparent;
  border-bottom: 3px solid transparent;
}

.target-info {
  display: flex;
  flex-direction: column;
}
.target-name {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}
.target-label {
  font-size: 11px;
  color: #64748b;
}

.relation-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}
.weight-control {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}
.weight-control .label {
  font-size: 10px;
  color: #94a3b8;
}

.btn-group {
  display: flex;
  gap: 8px;
}
</style>
