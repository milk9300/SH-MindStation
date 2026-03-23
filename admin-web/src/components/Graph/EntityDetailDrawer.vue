<template>
  <el-drawer
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    :title="`实体详情: ${node?.name || '加载中...'}`"
    size="55%"
    class="entity-drawer"
    destroy-on-close
  >
    <div v-if="node" v-loading="loading">
      <!-- 顶部：基础属性编辑卡片 -->
      <el-card shadow="never" class="property-card mb-6">
        <template #header>
          <div class="flex justify-between items-center header-row">
            <span class="font-bold">基础信息</span>
            <el-tag :type="getNodeTypeTag(node.label)">{{ node.label }}</el-tag>
          </div>
        </template>
        
        <el-form :model="node" label-position="top">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="UUID / 唯一标识 (不可更改)">
                <el-input v-model="node.uuid" disabled />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="名称">
                <el-input v-model="node.name" placeholder="请输入名称" />
              </el-form-item>
            </el-col>
          </el-row>
          
          <!-- 动态 Schema 表单区域 -->
          <div class="dynamic-form-container mt-4">
            <el-divider content-position="left">扩展业务属性</el-divider>
            
            <el-form-item 
              v-for="field in schema.fields" 
              :key="field.prop" 
              :label="field.label"
              class="schema-item"
            >
              <!-- 评分类型 -->
              <el-rate 
                v-if="field.type === 'rate'" 
                v-model="node.properties[field.prop]" 
                :max="5"
                show-score
                text-color="#ff9900"
              />
              
              <!-- 多行文本 -->
              <el-input
                v-else-if="field.type === 'textarea'"
                v-model="node.properties[field.prop]"
                type="textarea"
                :rows="4"
                :placeholder="field.placeholder || `请输入${field.label}...`"
              />

              <!-- 下拉选择 -->
              <el-select
                v-else-if="field.type === 'select'"
                v-model="node.properties[field.prop]"
                class="w-full"
              >
                <el-option
                  v-for="opt in field.options"
                  :key="opt.value"
                  :label="opt.label"
                  :value="opt.value"
                />
              </el-select>

              <!-- 数字输入 -->
              <el-input-number
                v-else-if="field.type === 'number'"
                v-model="node.properties[field.prop]"
                class="w-full"
              />
              
              <!-- 普通文本 (默认) -->
              <el-input
                v-else
                v-model="node.properties[field.prop]"
                :placeholder="field.placeholder || `请输入${field.label}...`"
              />
            </el-form-item>
          </div>

          <div class="flex gap-3 justify-end mt-4 action-footer">
            <el-button type="danger" plain @click="$emit('delete')">删除实体</el-button>
            <el-button type="primary" @click="$emit('save')">保存基础属性</el-button>
          </div>
        </el-form>
      </el-card>

      <!-- 下半部分：关系管理 Tabs -->
      <el-tabs :model-value="activeTab" @update:model-value="$emit('update:activeTab', $event)" class="relationship-tabs">
        <el-tab-pane label="具有症状" name="具有症状">
          <div class="tab-header">
            <span class="tab-desc">此问题关联的典型临床表现</span>
            <el-button type="primary" plain size="small" @click="$emit('open-bind', '具有症状')">+ 新增症状关联</el-button>
          </div>
          <RelationshipTable 
            :data="getRelationshipsByType('具有症状')" 
            @update-prop="(rel, val) => $emit('update-edge', rel, val)"
            @unlink="(rel) => $emit('unlink', rel)"
          />
        </el-tab-pane>

        <el-tab-pane label="治疗方案" name="治疗方案">
          <div class="tab-header">
            <span class="tab-desc">匹配的临床干预与治疗方案</span>
            <el-button type="primary" plain size="small" @click="$emit('open-bind', '治疗方案')">+ 新增方案关联</el-button>
          </div>
          <RelationshipTable 
            :data="getRelationshipsByType('治疗方案')" 
            @update-prop="(rel, val) => $emit('update-edge', rel, val)"
            @unlink="(rel) => $emit('unlink', rel)"
          />
        </el-tab-pane>

        <el-tab-pane label="推荐阅读/工具" name="recommend">
          <div class="tab-header">
            <span class="tab-desc">推荐的文章、测评量表等知识元</span>
            <div class="flex gap-2">
              <el-button type="success" plain size="small" @click="$emit('open-bind', '推荐文章')">+ 推荐文章</el-button>
              <el-button type="warning" plain size="small" @click="$emit('open-bind', '推荐测评')">+ 推荐量表</el-button>
            </div>
          </div>
          <RelationshipTable 
            :data="[...getRelationshipsByType('推荐文章'), ...getRelationshipsByType('推荐测评')]" 
            @update-prop="(rel, val) => $emit('update-edge', rel, val)"
            @unlink="(rel) => $emit('unlink', rel)"
          />
        </el-tab-pane>

        <el-tab-pane label="其他发散关系" name="others">
           <div class="tab-header">
            <span class="tab-desc">图谱中该节点发出的所有其他类型连线</span>
          </div>
          <RelationshipTable 
            :data="getOtherRelationships()" 
            @update-prop="(rel, val) => $emit('update-edge', rel, val)"
            @unlink="(rel) => $emit('unlink', rel)"
          />
        </el-tab-pane>
      </el-tabs>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import RelationshipTable from './RelationshipTable.vue'
import type { GraphNode, NodeSchema } from '../../types/graph'

const props = defineProps<{
  visible: boolean
  loading: boolean
  node: GraphNode | null
  schema: NodeSchema
  activeTab: string
  relationships: any[]
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'update:activeTab', val: string): void
  (e: 'save'): void
  (e: 'delete'): void
  (e: 'open-bind', type: string): void
  (e: 'unlink', rel: any): void
  (e: 'update-edge', rel: any, val: number): void
}>()

const getRelationshipsByType = (type: string) => {
  return props.relationships.filter((r: any) => r.type === type)
}

const getOtherRelationships = () => {
  const knownTypes = ['具有症状', '治疗方案', '推荐文章', '推荐测评']
  return props.relationships.filter((r: any) => !knownTypes.includes(r.type))
}

const getNodeTypeTag = (label: string) => {
  const map: any = { '心理问题': 'danger', '症状': 'warning', '治疗方案': 'success', '心理文章': 'info' }
  return map[label] || ''
}
</script>

<style scoped>
.mb-6 { margin-bottom: 24px; }
.property-card {
  border: none;
  background: #fdfdfd;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}
.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.dynamic-form-container { margin-top: 16px; }
.schema-item { margin-bottom: 20px; }
.action-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 16px;
}
.tab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  background: #f8fafc;
  padding: 8px 12px;
  border-radius: 6px;
}
.tab-desc {
  font-size: 13px;
  color: #64748b;
}
:deep(.el-drawer__body) {
  padding-top: 10px;
  background-color: #f8fafc;
}
</style>
