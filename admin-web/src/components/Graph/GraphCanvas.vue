<template>
  <el-card class="graph-card full-height" shadow="never">
    <template #header>
      <div class="card-header">
        <div class="header-title">图谱全貌预览 (AntV G6)</div>
        
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
          <el-button size="small" :icon="FullScreen" @click="fitGraph">自适应</el-button>
        </el-button-group>
      </div>
    </template>
    <div ref="graphRef" class="graph-canvas"></div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { Refresh, FullScreen } from '@element-plus/icons-vue'
import G6 from '@antv/g6'
import type { GraphData } from '../../types/graph'

const props = defineProps<{
  data: GraphData
  loading: boolean
  availableTypes: string[]
  selectedTypes: string[]
}>()

const emit = defineEmits<{
  (e: 'update:selectedTypes', val: string[]): void
  (e: 'node-click', nodeId: string): void
  (e: 'refresh'): void
  (e: 'create-node'): void
}>()

const graphRef = ref<HTMLElement | null>(null)
let graph: any = null

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
      emit('node-click', model.id)
    }
  })
}

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

const fitGraph = () => graph?.fitView()

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
</style>
