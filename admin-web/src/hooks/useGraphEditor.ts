import { ref, computed } from 'vue'
import type { GraphNode, GraphData } from '../types/graph'
import apiClient from '../utils/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getSchemaByLabel } from '../config/graphNodeSchema'

export function useGraphEditor() {
  const loading = ref(false)
  const rawGraphData = ref<GraphData>({ nodes: [], edges: [] })
  const availableTypes = ref<string[]>([])
  const selectedTypes = ref<string[]>([])
  
  const drawerVisible = ref(false)
  const drawerLoading = ref(false)
  const selectedNode = ref<GraphNode | null>(null)
  const activeTab = ref('具有症状')

  // --- 新节点创建 ---
  const createNodeDialogVisible = ref(false)
  const createNodeActionLoading = ref(false)

  // --- 搜索与绑定 ---
  const bindDialogVisible = ref(false)
  const currentRelType = ref('')
  const searchLoading = ref(false)
  const searchResults = ref<any[]>([])
  const bindActionLoading = ref(false)

  const colorMap: Record<string, string> = {
    '心理问题': '#0891b2', '症状': '#f59e0b', '治疗方案': '#22c55e', 
    '高危': '#ef4444', '风险等级': '#dc2626', '心理文章': '#8b5cf6',
    '应急预案': '#be123c', '应对技巧': '#10b981', '校园政策': '#0284c7', '校园机构': '#4338ca'
  }

  const currentSchema = computed(() => getSchemaByLabel(selectedNode.value?.label || ''))

  const fetchGraphData = async () => {
    loading.value = true
    try {
      const data: any = await apiClient.get('/graph/dump/')
      rawGraphData.value = {
        nodes: (data.nodes || []).map((n: any) => ({
          ...n,
          label: n.name,
          nodeType: n.label,
          style: { fill: colorMap[n.label] || '#e2e8f0', stroke: 'white', lineWidth: 2 }
        })),
        edges: data.edges || []
      }

      availableTypes.value = Array.from(new Set(rawGraphData.value.nodes.map(n => n.nodeType || '')))
      if (selectedTypes.value.length === 0 && availableTypes.value.includes('心理问题')) {
        selectedTypes.value = ['心理问题']
      } else if (selectedTypes.value.length === 0 && availableTypes.value.length > 0) {
        selectedTypes.value = [availableTypes.value[0]]
      }
    } catch (err) {
      ElMessage.error('获取图谱数据失败')
    } finally {
      loading.value = false
    }
  }

  const openEntityDrawer = async (nodeId: string) => {
    drawerVisible.value = true
    drawerLoading.value = true
    try {
      const res: any = await apiClient.get(`/graph/entity/${nodeId}/`)
      
      // 数据标准化：确保数值型属性被正确解析为 Number，防止 UI 显示 NaN
      if (res.properties) {
        if (res.properties['严重程度'] !== undefined) {
          res.properties['严重程度'] = Number(res.properties['严重程度']) || 0
        }
        if (res.properties['题目总数'] !== undefined) {
          res.properties['题目总数'] = Number(res.properties['题目总数']) || 0
        }
      }

      selectedNode.value = res
      if (res.label === '心理问题' || res.label === '症状') {
        activeTab.value = '具有症状'
      } else {
        activeTab.value = 'recommend'
      }
    } catch (e) {
      ElMessage.error('获取实体详情失败')
    } finally {
      drawerLoading.value = false
    }
  }

  const saveEntityChanges = async () => {
    if (!selectedNode.value) return
    try {
      const payload = {
        name: selectedNode.value.name,
        properties: selectedNode.value.properties
      }
      await apiClient.put(`/graph/entity/${selectedNode.value.id}/`, payload)
      ElMessage.success('基础属性保存成功')
      fetchGraphData()
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

  const handleUnlink = async (rel: any) => {
    if (!selectedNode.value) return
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
      openEntityDrawer(selectedNode.value.id)
    } catch (e) {}
  }

  const handleUpdateEdgeProp = async (rel: any, val: number) => {
    if (!selectedNode.value) return
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

  const confirmCreateNode = async (data: { label: string, name: string }) => {
    if (!data.name.trim()) return ElMessage.warning('请输入实体名称')
    try {
      createNodeActionLoading.value = true
      const res: any = await apiClient.post('/graph/entity/create/', data)
      ElMessage.success(res.message)
      createNodeDialogVisible.value = false
      await fetchGraphData()
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

  const confirmBind = async (data: { targetUuid: string, weight: number }) => {
    if (!selectedNode.value || !data.targetUuid) return
    bindActionLoading.value = true
    try {
      const properties: any = {}
      if (currentRelType.value === '具有症状') properties['匹配权重'] = data.weight
      if (currentRelType.value === '治疗方案') properties['有效性'] = data.weight

      await apiClient.post('/graph/edge/', {
        source_id: selectedNode.value.id,
        target_uuid: data.targetUuid,
        rel_type: currentRelType.value,
        properties
      })
      ElMessage.success('关联成功')
      bindDialogVisible.value = false
      openEntityDrawer(selectedNode.value.id)
    } catch (e) {
      ElMessage.error('绑定失败')
    } finally {
      bindActionLoading.value = false
    }
  }

  return {
    loading,
    rawGraphData,
    availableTypes,
    selectedTypes,
    drawerVisible,
    drawerLoading,
    selectedNode,
    activeTab,
    currentSchema,
    createNodeDialogVisible,
    createNodeActionLoading,
    bindDialogVisible,
    currentRelType,
    searchLoading,
    searchResults,
    bindActionLoading,
    fetchGraphData,
    openEntityDrawer,
    saveEntityChanges,
    deleteEntity,
    handleUnlink,
    handleUpdateEdgeProp,
    confirmCreateNode,
    searchNodes,
    confirmBind
  }
}
