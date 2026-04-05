<template>
  <el-card class="graph-card full-height" shadow="never">
    <template #header>
      <div class="card-header">
        <div class="header-title">图谱交互探索 (AntV G6)</div>
        
        <div class="filter-group" v-if="availableTypes.length > 0">
          <el-checkbox-group :model-value="selectedTypes" @change="$emit('update:selectedTypes', $event)" size="small">
            <el-checkbox-button v-for="type in availableTypes" :key="type" :label="type">
              {{ type }}
            </el-checkbox-button>
          </el-checkbox-group>
        </div>

        <el-button-group>
          <el-button type="success" size="small" @click="$emit('create-node')">+ 新增实体节点</el-button>
          <el-button type="primary" size="small" @click="$emit('refresh')" :loading="loading" :icon="Refresh">刷新图谱</el-button>
          <el-button type="warning" size="small" @click="clearCanvas" :icon="Delete">清空画布</el-button>
          <el-button size="small" :icon="FullScreen" @click="fitGraph">自适应</el-button>
        </el-button-group>
      </div>
    </template>
    <div class="canvas-container">
      <div class="canvas-search-box">
        <el-autocomplete
          v-model="searchQuery"
          :fetch-suggestions="querySearch"
          placeholder="搜索实体以探索..."
          class="search-input"
          size="default"
          @select="handleSearchSelect"
          :prefix-icon="Search"
          clearable
        >
          <template #default="{ item }">
            <div class="search-item">
              <span class="name">{{ item.name }}</span>
              <el-tag size="small" :type="getTagType(item.label)" class="label-tag">{{ item.label }}</el-tag>
            </div>
          </template>
        </el-autocomplete>
      </div>
      <div ref="graphRef" class="graph-canvas"></div>
      
      <!-- 右键浮动菜单 -->
      <div 
        v-show="menuVisible" 
        class="context-menu" 
        :style="{ left: menuX + 'px', top: menuY + 'px' }"
      >
        <div class="menu-item" @click="handleMenuAction('detail')">
          <el-icon><Warning /></el-icon> 查看编辑详情
        </div>
        <div class="menu-item" @click="handleMenuAction('expand')">
          <el-icon><Operation /></el-icon> 扩展关联节点
        </div>
        <div class="menu-item" @click="handleMenuAction('locate')">
          <el-icon><Location /></el-icon> 中心聚焦
        </div>
        <div class="menu-divider"></div>
        <div class="menu-item danger" @click="handleMenuAction('remove')">
          <el-icon><Delete /></el-icon> 从画布移除
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { Refresh, FullScreen, Search, Delete, Warning, Operation, Location } from '@element-plus/icons-vue'
import G6 from '@antv/g6'
import { ElMessage } from 'element-plus'
import type { GraphData } from '../../types/graph'

const props = defineProps<{
  data: GraphData
  loading: boolean
  availableTypes: string[]
  selectedTypes: string[]
  fetchNeighbors?: (nodeId: string) => Promise<GraphData>
  searchResults?: any[]
  searchLoading?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:selectedTypes', val: string[]): void
  (e: 'node-click', nodeId: string): void
  (e: 'refresh'): void
  (e: 'create-node'): void
  (e: 'search', q: string): void
}>()

const graphRef = ref<HTMLElement | null>(null)
let graph: any = null

// 右键菜单状态
const menuVisible = ref(false)
const menuX = ref(0)
const menuY = ref(0)
const contextNode = ref<any>(null)

const initGraph = () => {
  if (!graphRef.value) return
  graph = new G6.Graph({
    container: graphRef.value,
    width: graphRef.value.offsetWidth,
    height: graphRef.value.offsetHeight || 600,
    fitView: true,
    fitViewPadding: [40, 40, 40, 40],
    animate: false,
    defaultNode: {
      type: 'circle',
      size: 55,
      labelCfg: { position: 'bottom', offset: 5, style: { fill: '#334155', fontSize: 12 } }
    },
    defaultEdge: {
      type: 'quadratic',
      style: { stroke: '#e2e8f0', lineWidth: 1.5, opacity: 0.6, endArrow: true },
      labelCfg: { autoRotate: true, style: { fill: '#94a3b8', fontSize: 9, background: { fill: '#fff', padding: [2, 4] } } }
    },
    layout: {
      type: 'force',
      preventOverlap: true,
      linkDistance: 180,
      nodeStrength: -150,
      edgeStrength: 0.5,
      alphaDecay: 0.05, // 加快收敛
    } as any,
    modes: {
      default: [
        { type: 'drag-canvas', enableOptimize: true },
        { type: 'zoom-canvas', enableOptimize: true },
        'drag-node'
      ]
    }
  })

  // --- LOD 视距细节优化 (节流处理) ---
  let timer: any = null
  graph.on('viewportchange', () => {
    if (timer) return
    timer = setTimeout(() => {
      const zoom = graph.getZoom()
      const showLabel = zoom >= 0.4
      
      graph.getNodes().forEach((node: any) => {
        const model = node.getModel()
        if (!!model.label !== showLabel) {
          graph.updateItem(node, {
            label: showLabel ? node.get('model').name : ''
          })
        }
      })
      timer = null
    }, 100)
  })

  graph.on('node:click', (evt: any) => {
    hideMenu()
    const nodeItem = evt.item
    const model = nodeItem?.getModel()
    if (!model) return

    // 单击仅触发打开详情，不再自动扩展邻居
    emit('node-click', model.id)
  })

  // 双击扩展邻居
  graph.on('node:dblclick', async (evt: any) => {
    const nodeItem = evt.item
    const model = nodeItem?.getModel()
    if (!model) return
    expandNode(model)
  })

  // 右键菜单
  graph.on('node:contextmenu', (evt: any) => {
    evt.preventDefault()
    evt.stopPropagation()
    
    const model = evt.item.getModel()
    contextNode.value = model
    
    // 计算菜单位置 (考虑画布偏移和 Canvas 容器)
    const canvasRect = graphRef.value!.getBoundingClientRect()
    menuX.value = evt.clientX - canvasRect.left + 5
    menuY.value = evt.clientY - canvasRect.top + 5
    menuVisible.value = true
  })

  // 点击空白处隐藏菜单
  graph.on('canvas:click', () => hideMenu())
  graph.on('wheelzoom', () => hideMenu())
  graph.on('canvas:drag', () => hideMenu())
}

const hideMenu = () => {
  menuVisible.value = false
}

const handleMenuAction = async (action: string) => {
  if (!contextNode.value) return
  const node = contextNode.value
  hideMenu()

  switch (action) {
    case 'detail':
      emit('node-click', node.id)
      break
    case 'expand':
      expandNode(node)
      break
    case 'locate':
      locateNode(node.id)
      break
    case 'remove':
      graph.removeItem(node.id)
      break
  }
}

const expandNode = async (model: any) => {
  if (!props.fetchNeighbors) return
  
  try {
    const { nodes, edges } = await props.fetchNeighbors(model.id)
    
    // 过滤掉已存在的节点
    const currentNodes = new Set(graph.getNodes().map((n: any) => n.get('id')))
    nodes.forEach((n: any) => {
      if (!currentNodes.has(n.id)) {
        graph.addItem('node', n)
      }
    })

    // 过滤掉已存在的边
    const currentEdges = new Set(graph.getEdges().map((e: any) => `${e.getModel().source}-${e.getModel().target}`))
    edges.forEach((e: any) => {
      const edgeKey = `${e.source}-${e.target}`
      if (!currentEdges.has(edgeKey)) {
        graph.addItem('edge', e)
      }
    })

    graph.layout()
    nextTick(() => {
      ElMessage.success(`已扩展 ${nodes.length} 个关联节点`)
    })
  } catch (err) {
    ElMessage.error('扩展节点失败')
  }
}

const fitGraph = () => graph?.fitView()

const renderGraph = () => {
  if (!graph || !props.data) return
  
  // 使用深拷贝防止 G6 修改原始响应式数据
  const clonedData = JSON.parse(JSON.stringify(props.data))
  
  // 优化：如果已经有数据且不是首次渲染，尝试使用 changeData 平滑更新
  // 但对于力导向布局，有时直接 render 反而更稳
  if (graph.getNodes().length > 0) {
    graph.changeData(clonedData)
  } else {
    graph.data(clonedData)
    graph.render()
  }
}

const searchQuery = ref('')
const querySearch = (queryString: string, cb: any) => {
  if (!queryString) return cb([])
  emit('search', queryString)
  // 简单轮询/等待机制，因为 props 是异步更新的
  const checkResults = () => {
    if (props.searchResults && props.searchResults.length > 0) {
      cb(props.searchResults)
    } else {
      setTimeout(checkResults, 100)
    }
  }
  checkResults()
}

const handleSearchSelect = async (item: any) => {
  if (!graph || !item) return
  searchQuery.value = item.name
  
  // 1. 优先获取邻居，实现批量添加
  let neighborData: GraphData = { nodes: [], edges: [] }
  if (props.fetchNeighbors) {
    neighborData = await props.fetchNeighbors(item.id)
  }

  // 2. 批量将节点和边加入画布
  const nodesToAdd = [item, ...neighborData.nodes]
  nodesToAdd.forEach(n => {
    if (!graph.findById(n.id)) {
      graph.addItem('node', n)
    }
  })

  neighborData.edges.forEach(e => {
    const exists = graph.getEdges().some((edge: any) => {
      const m = edge.getModel()
      return m.source === e.source && m.target === e.target && (m as any).label === (e as any).label
    })
    if (!exists) {
      graph.addItem('edge', e)
    }
  })

  // 3. 统一触发一次布局
  graph.layout()
  
  // 4. 定位到目标节点
  setTimeout(() => {
    const target = graph.findById(item.id)
    if (target) {
      graph.focusItem(target, true, { easing: 'easeCubic', duration: 800 })
      graph.zoomTo(1.0, { x: target.getModel().x, y: target.getModel().y })
    }
  }, 500)
}

const clearCanvas = () => {
  if (!graph) return
  graph.clear()
  emit('refresh') // 触发重新拉取 root 节点
}

const locateNode = (id: string | number) => {
  if (!graph) return
  const item = graph.findById(id)
  if (item) {
    graph.focusItem(item, true, { easing: 'easeCubic', duration: 800 })
    graph.zoomTo(1.2, { x: item.getModel().x, y: item.getModel().y })
    // 闪烁高亮一下
    graph.setItemState(item, 'highlight', true)
    setTimeout(() => graph.setItemState(item, 'highlight', false), 2000)
  }
}

// 暴露方法给父组件
defineExpose({
  locateNode
})

const getTagType = (label: string) => {
  const map: any = { '心理问题': 'danger', '症状': 'warning', '治疗方案': 'success' }
  return map[label] || 'info'
}

watch(() => props.data, () => {
  renderGraph()
}, { deep: true })

onMounted(() => {
  // 确保 DOM 已经完全计算尺寸
  const observer = new ResizeObserver(() => {
    if (graph && graphRef.value) {
      const width = graphRef.value.offsetWidth
      const height = graphRef.value.offsetHeight || 600
      graph.changeSize(width, height)
      graph.setAutoPaint(true)
      graph.paint()
      graph.fitView()
    }
  })

  setTimeout(() => {
    initGraph()
    renderGraph()
    if (graphRef.value) observer.observe(graphRef.value)
  }, 200)
})

onBeforeUnmount(() => graph?.destroy())
</script>

<style scoped>
.full-height { height: 100%; }
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.canvas-container {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
}
.canvas-search-box {
  position: absolute;
  top: 24px;
  left: 24px;
  z-index: 100;
  width: 340px;
  background: white;
  padding: 4px;
  border-radius: 8px;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
  border: 1px solid #e2e8f0;
}
.search-input :deep(.el-input__wrapper) {
  box-shadow: none !important;
  background: transparent;
}
.search-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 4px;
}
.search-item .name {
  font-weight: 500;
  color: #0f172a;
  font-size: 14px;
}
.label-tag {
  border-radius: 4px;
  font-weight: 600;
  text-transform: uppercase;
  font-size: 10px;
}
.graph-canvas {
  width: 100%;
  height: 100%;
  background: radial-gradient(circle, #f8fafc 10%, #f1f5f9 100%);
}

/* 右键菜单样式 */
.context-menu {
  position: absolute;
  z-index: 1000;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 6px;
  min-width: 160px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  font-size: 13px;
  color: #475569;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.menu-item:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.menu-item.danger {
  color: #ef4444;
}

.menu-item.danger:hover {
  background: #fef2f2;
  color: #dc2626;
}

.menu-item .el-icon {
  font-size: 16px;
}

.menu-divider {
  height: 1px;
  background: #f1f5f9;
  margin: 4px 8px;
}
</style>
