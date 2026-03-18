<template>
  <div class="entity-editor-container">
    <!-- 全屏图谱可视化区域 -->
    <el-card class="graph-card full-height" shadow="never">
      <template #header>
        <div class="card-header">
          <div class="header-title">图谱全貌预览 (AntV G6)</div>
          
          <div class="filter-group" v-if="availableTypes.length > 0">
            <el-checkbox-group v-model="selectedTypes" @change="applyFilters" size="small">
              <el-checkbox-button v-for="type in availableTypes" :key="type" :label="type">
                {{ type }}
              </el-checkbox-button>
            </el-checkbox-group>
          </div>

          <el-button-group>
            <el-button type="success" size="small" @click="openCreateNodeDialog">+ 新增实体节点</el-button>
            <el-button type="primary" size="small" @click="fetchGraphData" :icon="Refresh">刷新图谱</el-button>
            <el-button size="small" :icon="FullScreen" @click="fitGraph">自适应</el-button>
          </el-button-group>
        </div>
      </template>
      <div id="graph-container" ref="graphRef" class="graph-canvas"></div>
    </el-card>

<!-- 关系管理通用表格组件模板 -->
    <template id="relationship-table-tpl">
      <el-table :data="tableData" border size="small" style="width: 100%">
        <el-table-column prop="target_name" label="目标节点名称" min-width="150" />
        <el-table-column prop="type" label="关系类型" width="100" />
        <el-table-column label="权重 / 属性" width="180">
          <template #default="scope">
            <el-input-number
              v-if="scope.row.properties['匹配权重'] !== undefined || scope.row.properties['有效性'] !== undefined"
              :model-value="scope.row.properties['匹配权重'] || scope.row.properties['有效性']"
              :min="0.1" :max="1.0" :step="0.1" size="small"
              @update:model-value="(val) => $emit('update-prop', scope.row, val)"
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

    <!-- 360° 实体详情与关系编辑抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      :title="`实体详情: ${selectedNode?.name || '加载中...'}`"
      size="55%"
      class="entity-drawer"
      destroy-on-close
    >
      <div v-if="selectedNode" v-loading="drawerLoading">
        <!-- 顶部：基础属性编辑卡片 -->
        <el-card shadow="never" class="property-card mb-6">
          <template #header>
            <div class="flex justify-between items-center">
              <span class="font-bold">基础信息</span>
              <el-tag :type="getNodeTypeTag(selectedNode.label)">{{ selectedNode.label }}</el-tag>
            </div>
          </template>
          
          <el-form :model="selectedNode" label-position="top">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="UUID / 唯一标识 (不可更改)">
                  <el-input v-model="selectedNode.uuid" disabled />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="名称">
                  <el-input v-model="selectedNode.name" placeholder="请输入名称" />
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-form-item label="详细描述 / 内容摘要">
              <el-input
                v-model="selectedNode.properties.描述"
                v-if="selectedNode.properties.描述 !== undefined"
                type="textarea"
                :rows="4"
              />
              <el-input
                v-model="selectedNode.properties.原理"
                v-else-if="selectedNode.properties.原理 !== undefined"
                type="textarea"
                :rows="4"
              />
              <el-input
                v-model="selectedNode.properties.诊断标准"
                v-else-if="selectedNode.properties.诊断标准 !== undefined"
                type="textarea"
                :rows="4"
              />
              <el-input
                v-else
                v-model="selectedNode.description"
                type="textarea"
                :rows="4"
              />
            </el-form-item>

            <div class="flex gap-3 justify-end mt-4">
              <el-button type="danger" plain @click="deleteEntity">删除实体</el-button>
              <el-button type="primary" @click="saveEntityChanges">保存基础属性</el-button>
            </div>
          </el-form>
        </el-card>

        <!-- 下半部分：关系管理 Tabs -->
        <el-tabs v-model="activeTab" class="relationship-tabs">
          <!-- 1. 对应不同关系类型的 Tab 视图 -->
          <el-tab-pane label="具有症状" name="具有症状">
            <div class="tab-header">
              <span class="tab-desc">此问题关联的典型临床表现</span>
              <el-button type="primary" plain size="small" @click="openBindDialog('具有症状')">+ 新增症状关联</el-button>
            </div>
            <!-- 内联表格组件 -->
            <el-table :data="getRelationshipsByType('具有症状')" border size="small" style="width: 100%">
              <el-table-column prop="target_name" label="目标节点名称" min-width="150" />
              <el-table-column prop="type" label="关系类型" width="100" />
              <el-table-column label="权重 / 属性" width="180">
                <template #default="scope">
                  <el-input-number
                    v-if="scope.row.properties['匹配权重'] !== undefined || scope.row.properties['有效性'] !== undefined"
                    :model-value="scope.row.properties['匹配权重'] || scope.row.properties['有效性']"
                    :min="0.1" :max="1.0" :step="0.1" size="small"
                    @change="(val) => handleUpdateEdgeProp(scope.row, val)"
                  />
                  <span v-else class="text-gray-400">无权值属性</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80" align="center">
                <template #default="scope">
                  <el-button type="danger" link size="small" @click="handleUnlink(scope.row)">解绑</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="治疗方案" name="治疗方案">
            <div class="tab-header">
              <span class="tab-desc">匹配的临床干预与治疗方案</span>
              <el-button type="primary" plain size="small" @click="openBindDialog('治疗方案')">+ 新增方案关联</el-button>
            </div>
            <el-table :data="getRelationshipsByType('治疗方案')" border size="small" style="width: 100%">
              <el-table-column prop="target_name" label="目标节点名称" min-width="150" />
              <el-table-column prop="type" label="关系类型" width="100" />
              <el-table-column label="权重 / 属性" width="180">
                <template #default="scope">
                  <el-input-number
                    v-if="scope.row.properties['匹配权重'] !== undefined || scope.row.properties['有效性'] !== undefined"
                    :model-value="scope.row.properties['匹配权重'] || scope.row.properties['有效性']"
                    :min="0.1" :max="1.0" :step="0.1" size="small"
                    @change="(val) => handleUpdateEdgeProp(scope.row, val)"
                  />
                  <span v-else class="text-gray-400">无权值属性</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80" align="center">
                <template #default="scope">
                  <el-button type="danger" link size="small" @click="handleUnlink(scope.row)">解绑</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="推荐阅读/工具" name="recommend">
            <div class="tab-header">
              <span class="tab-desc">推荐的文章、测评量表等知识元</span>
              <div class="flex gap-2">
                <el-button type="success" plain size="small" @click="openBindDialog('推荐文章')">+ 推荐文章</el-button>
                <el-button type="warning" plain size="small" @click="openBindDialog('推荐测评')">+ 推荐量表</el-button>
              </div>
            </div>
            <el-table :data="[...getRelationshipsByType('推荐文章'), ...getRelationshipsByType('推荐测评')]" border size="small" style="width: 100%">
              <el-table-column prop="target_name" label="目标节点名称" min-width="150" />
              <el-table-column prop="type" label="关系类型" width="100" />
              <el-table-column label="权重 / 属性" width="180">
                <template #default="scope">
                  <el-input-number
                    v-if="scope.row.properties['匹配权重'] !== undefined || scope.row.properties['有效性'] !== undefined"
                    :model-value="scope.row.properties['匹配权重'] || scope.row.properties['有效性']"
                    :min="0.1" :max="1.0" :step="0.1" size="small"
                    @change="(val) => handleUpdateEdgeProp(scope.row, val)"
                  />
                  <span v-else class="text-gray-400">无权值属性</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80" align="center">
                <template #default="scope">
                  <el-button type="danger" link size="small" @click="handleUnlink(scope.row)">解绑</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="其他发散关系" name="others">
             <div class="tab-header">
              <span class="tab-desc">图谱中该节点发出的所有其他类型连线</span>
            </div>
            <el-table :data="getOtherRelationships()" border size="small" style="width: 100%">
              <el-table-column prop="target_name" label="目标节点名称" min-width="150" />
              <el-table-column prop="type" label="关系类型" width="100" />
              <el-table-column label="权重 / 属性" width="180">
                <template #default="scope">
                   <span class="text-gray-400">暂无属性展示</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80" align="center">
                <template #default="scope">
                  <el-button type="danger" link size="small" @click="handleUnlink(scope.row)">解绑</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-drawer>

    <!-- 新增实体节点对话框 -->
    <el-dialog v-model="createNodeDialogVisible" title="新增知识图谱实体节点" width="450px" append-to-body>
      <el-form :model="newNodeData" label-position="top" @submit.prevent="confirmCreateNode">
        <el-form-item label="实体类别 (Label)" required>
          <el-select v-model="newNodeData.label" class="w-full">
            <el-option label="心理问题" value="心理问题" />
            <el-option label="症状" value="症状" />
            <el-option label="干预方案" value="干预方案" />
            <el-option label="应对技巧" value="应对技巧" />
            <el-option label="风险等级" value="风险等级" />
            <el-option label="应急预案" value="应急预案" />
            <el-option label="校园部门" value="校园部门" />
          </el-select>
        </el-form-item>
        <el-form-item label="实体名称 (Name)" required>
          <el-input v-model="newNodeData.name" placeholder="请输入节点核心名称..." @keyup.enter="confirmCreateNode" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createNodeDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="createNodeActionLoading" @click="confirmCreateNode">确认建立新节点</el-button>
      </template>
    </el-dialog>

    <!-- 关联节点搜索 Dialog -->
    <el-dialog v-model="bindDialogVisible" :title="`新增 [${currentRelType}] 关联`" width="450px" append-to-body>
      <div class="p-4">
        <div class="mb-4 text-gray-500 text-sm">选择目标节点进行逻辑绑定：</div>
        <el-select
          v-model="selectedTargetUuid"
          filterable
          remote
          reserve-keyword
          placeholder="输入节点名称模糊搜索..."
          :remote-method="searchNodes"
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
        
        <div class="mt-6" v-if="currentRelType === '具有症状' || currentRelType === '治疗方案'">
          <div class="mb-2 text-sm text-gray-600">设置关联权重 (0.1 - 1.0):</div>
          <el-slider v-model="newRelWeight" :min="0.1" :max="1.0" :step="0.1" show-input />
        </div>
      </div>
      <template #footer>
        <el-button @click="bindDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="bindActionLoading" @click="confirmBind">确认建立关联</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, defineComponent, h } from 'vue'
import { Refresh, FullScreen, Delete } from '@element-plus/icons-vue'
import G6 from '@antv/g6'
import { ElMessage, ElMessageBox } from 'element-plus'
import apiClient from '../utils/api'

// removed RelationshipTable functional component

// ======= 核心逻辑 =======
const graphRef = ref<HTMLElement | null>(null)
let graph: any = null

const drawerVisible = ref(false)
const drawerLoading = ref(false)
const selectedNode = ref<any | null>(null)
const activeTab = ref('具有症状')

const loading = ref(false)
const availableTypes = ref<string[]>([])
const selectedTypes = ref<string[]>([])
const rawGraphData = ref<{nodes: any[], edges: any[]}>({nodes: [], edges: []})

// --- 新节点创建变量 ---
const createNodeDialogVisible = ref(false)
const createNodeActionLoading = ref(false)
const newNodeData = ref({ label: '症状', name: '' })

// --- 搜索与绑定变量 ---
const bindDialogVisible = ref(false)
const currentRelType = ref('')
const searchLoading = ref(false)
const searchResults = ref<any[]>([])
const selectedTargetUuid = ref('')
const newRelWeight = ref(0.8)
const bindActionLoading = ref(false)

// ======= 初始化与数据加载 =======
const initGraph = () => {
  if (!graphRef.value) return
  graph = new G6.Graph({
    container: graphRef.value,
    width: graphRef.value.offsetWidth,
    height: graphRef.value.offsetHeight || 600,
    fitView: true,
    fitViewPadding: [40, 40, 40, 40],
    defaultNode: {
      type: 'circle',
      size: 45,
      labelCfg: { position: 'center', style: { fill: '#fff', fontSize: 10 } }
    },
    defaultEdge: {
      type: 'quadratic',
      style: { stroke: '#e2e8f0', lineWidth: 1.5, opacity: 0.6, endArrow: true },
      labelCfg: { autoRotate: true, style: { fill: '#94a3b8', fontSize: 9, background: { fill: '#fff', padding: [2, 4] } } }
    },
    layout: {
      type: 'force',
      preventOverlap: true,
      linkDistance: 150,
      nodeStrength: -80,
    } as any,
    modes: {
      default: ['drag-canvas', 'zoom-canvas', 'drag-node']
    }
  })

  graph.on('node:click', (evt: any) => {
    const nodeItem = evt.item
    const model = nodeItem?.getModel()
    if (model) {
      openEntityDrawer(model.id)
    }
  })
}

const openEntityDrawer = async (nodeId: string) => {
  drawerVisible.value = true
  drawerLoading.value = true
  try {
    const res: any = await apiClient.get(`/graph/entity/${nodeId}/`)
    selectedNode.value = res
    // 根据节点类型设置默认 Tab
    if (res.label === '心理问题') activeTab.value = '具有症状'
    else if (res.label === '症状') activeTab.value = '具有症状'
    else activeTab.value = 'recommend'
  } catch (e) {
    ElMessage.error('获取实体详情失败')
  } finally {
    drawerLoading.value = false
  }
}

const fetchGraphData = async () => {
  loading.value = true
  try {
    const data: any = await apiClient.get('/graph/dump/')
    const colorMap: Record<string, string> = {
      '心理问题': '#0891b2', '症状': '#f59e0b', '治疗方案': '#22c55e', 
      '高危': '#ef4444', '风险等级': '#dc2626', '心理文章': '#8b5cf6',
      '应急预案': '#be123c', '应对技巧': '#10b981', '校园政策': '#0284c7', '校园机构': '#4338ca'
    }

    rawGraphData.value = {
      nodes: (data.nodes || []).map((n: any) => ({
        ...n,
        label: n.name,
        nodeType: n.label,
        style: { fill: colorMap[n.label] || '#e2e8f0', stroke: 'white', lineWidth: 2 }
      })),
      edges: data.edges || []
    }

    availableTypes.value = Array.from(new Set(rawGraphData.value.nodes.map(n => n.nodeType)))
    // 默认只展示 "心理问题"，防止整张大网一次性渲染导致前端严重卡顿
    selectedTypes.value = ['心理问题'].filter(t => availableTypes.value.includes(t))
    if (selectedTypes.value.length === 0 && availableTypes.value.length > 0) {
      selectedTypes.value = [availableTypes.value[0]] // 回退到任一可用类型
    }

    applyFilters()
  } catch (err) {
    ElMessage.error('获取图谱数据失败')
  } finally {
    loading.value = false
  }
}

const applyFilters = () => {
  if (!graph) return
  const filteredNodes = rawGraphData.value.nodes.filter(n => selectedTypes.value.includes(n.nodeType))
  const validNodeIds = new Set(filteredNodes.map(n => n.id))
  const filteredEdges = rawGraphData.value.edges.filter(e => validNodeIds.has(e.source) && validNodeIds.has(e.target))
  graph.data({ nodes: filteredNodes, edges: filteredEdges })
  graph.render()
}

// ======= 属性与关系操作 =======
const saveEntityChanges = async () => {
  if (!selectedNode.value) return
  try {
    const payload = {
      name: selectedNode.value.name,
      description: selectedNode.value.properties.描述 || selectedNode.value.properties.原理 || selectedNode.value.properties.诊断标准 || selectedNode.value.description
    }
    await apiClient.put(`/graph/entity/${selectedNode.value.id}/`, payload)
    ElMessage.success('基础属性保存成功')
    fetchGraphData() // 刷新画布
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

const deleteEntity = async () => {
  if (!selectedNode.value) return
  try {
    await ElMessageBox.confirm(`确定要彻底删除 [${selectedNode.value.name}] 吗？`, '危险操作', { type: 'warning' })
    await apiClient.delete(`/graph/entity/${selectedNode.value.id}/`)
    ElMessage.success('实体已删除')
    drawerVisible.value = false
    fetchGraphData()
  } catch (e) {}
}

const getRelationshipsByType = (type: string) => {
  if (!selectedNode.value) return []
  return selectedNode.value.relationships.filter((r: any) => r.type === type)
}

const getOtherRelationships = () => {
  if (!selectedNode.value) return []
  const knownTypes = ['具有症状', '治疗方案', '推荐文章', '推荐测评']
  return selectedNode.value.relationships.filter((r: any) => !knownTypes.includes(r.type))
}

const handleUnlink = async (rel: any) => {
  try {
    await ElMessageBox.confirm(`确定解绑与 [${rel.target_name}] 的关联吗？`, '提示')
    await apiClient.delete('/graph/edge/', {
      params: {
        source_id: selectedNode.value.id,
        target_uuid: rel.target_uuid,
        rel_type: rel.type
      }
    })
    ElMessage.success('关系已解除')
    openEntityDrawer(selectedNode.value.id) // 局部刷新详情
  } catch (e) {}
}

const handleUpdateEdgeProp = async (rel: any, val: number) => {
  try {
    const propKey = rel.type === '具有症状' ? '匹配权重' : '有效性'
    await apiClient.post('/graph/edge/', {
      source_id: selectedNode.value.id,
      target_uuid: rel.target_uuid,
      rel_type: rel.type,
      properties: { [propKey]: val }
    })
    ElMessage.success('权重已更新')
    openEntityDrawer(selectedNode.value.id)
  } catch (e) {}
}

// --- 搜索绑定 ---
const openBindDialog = (type: string) => {
  currentRelType.value = type
  searchResults.value = []
  selectedTargetUuid.value = ''
  bindDialogVisible.value = true
}

const openCreateNodeDialog = () => {
  newNodeData.value = { label: '症状', name: '' }
  createNodeDialogVisible.value = true
}

const confirmCreateNode = async () => {
  if (!newNodeData.value.name.trim()) {
    return ElMessage.warning('请输入实体名称')
  }
  try {
    createNodeActionLoading.value = true
    const res: any = await apiClient.post('/graph/entity/create/', newNodeData.value)
    ElMessage.success(res.message)
    createNodeDialogVisible.value = false
    await fetchGraphData() // 刷新图谱以显示这只新节点
  } catch (err: any) {
    ElMessage.error(err.response?.data?.error || '创建节点失败')
  } finally {
    createNodeActionLoading.value = false
  }
}

const searchNodes = async (q: string) => {
  if (!q) return
  searchLoading.value = true
  try {
    const res: any = await apiClient.get('/graph/search/', { params: { q } })
    searchResults.value = res
  } finally {
    searchLoading.value = false
  }
}

const confirmBind = async () => {
  if (!selectedTargetUuid.value) return
  bindActionLoading.value = true
  try {
    const properties: any = {}
    if (currentRelType.value === '具有症状') properties['匹配权重'] = newRelWeight.value
    if (currentRelType.value === '治疗方案') properties['有效性'] = newRelWeight.value

    await apiClient.post('/graph/edge/', {
      source_id: selectedNode.value.id,
      target_uuid: selectedTargetUuid.value,
      rel_type: currentRelType.value,
      properties
    })
    ElMessage.success('关联成功')
    bindDialogVisible.value = false
    openEntityDrawer(selectedNode.value.id) // 刷新详情
  } catch (e) {
    ElMessage.error('绑定失败')
  } finally {
    bindActionLoading.value = false
  }
}

const getNodeTypeTag = (label: string) => {
  const map: any = { '心理问题': 'danger', '症状': 'warning', '治疗方案': 'success', '心理文章': 'info' }
  return map[label] || ''
}

const fitGraph = () => graph?.fitView()

onMounted(() => {
  setTimeout(() => {
    initGraph()
    fetchGraphData()
  }, 100)
  window.addEventListener('resize', () => {
    if (graph && graphRef.value) graph.changeSize(graphRef.value.offsetWidth, graphRef.value.offsetHeight)
  })
})
onBeforeUnmount(() => graph?.destroy())
</script>

<style scoped>
.entity-editor-container {
  height: calc(100vh - 120px);
}
.full-height { height: 100%; }
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.filter-group {
  flex: 1;
  display: flex;
  justify-content: center;
  padding: 0 20px;
}
.graph-canvas {
  width: 100%;
  height: 100%;
  background: radial-gradient(circle, #f8fafc 10%, #f1f5f9 100%);
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
.mb-6 { margin-bottom: 24px; }
.property-card {
  border: none;
  background: #fdfdfd;
}
:deep(.el-drawer__body) {
  padding-top: 10px;
}
</style>
