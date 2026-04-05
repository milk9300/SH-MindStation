<template>
  <div class="entity-editor-container">
    <GraphCanvas
      ref="graphCanvasRef"
      :data="filteredGraphData"
      :loading="loading"
      :available-types="availableTypes"
      v-model:selected-types="selectedTypes"
      :fetch-neighbors="fetchNeighbors"
      :search-results="searchResults"
      :search-loading="searchLoading"
      @node-click="openEntityDrawer"
      @refresh="fetchGraphData('initial')"
      @search="searchNodes"
      @create-node="createNodeDialogVisible = true"
    />

    <EntityDetailDrawer
      v-model:visible="drawerVisible"
      v-model:active-tab="activeTab"
      :loading="drawerLoading"
      :node="selectedNode"
      :schema="currentSchema"
      :relationships="selectedNode?.relationships || []"
      @save="saveEntityChanges"
      @delete="deleteEntity"
      @unlink="handleUnlink"
      @update-edge="handleUpdateEdgeProp"
      @open-bind="(type) => { currentRelType = type; bindDialogVisible = true }"
      @locate="handleLocateNode"
    />

    <CreateNodeDialog
      v-model:visible="createNodeDialogVisible"
      :loading="createNodeActionLoading"
      @confirm="confirmCreateNode"
    />

    <BindRelationDialog
      v-model:visible="bindDialogVisible"
      :rel-type="currentRelType"
      :search-results="searchResults"
      :search-loading="searchLoading"
      :confirm-loading="bindActionLoading"
      @search="searchNodes"
      @confirm="confirmBind"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import GraphCanvas from '../components/Graph/GraphCanvas.vue'
import EntityDetailDrawer from '../components/Graph/EntityDetailDrawer.vue'
import CreateNodeDialog from '../components/Graph/CreateNodeDialog.vue'
import BindRelationDialog from '../components/Graph/BindRelationDialog.vue'
import { useGraphEditor } from '../hooks/useGraphEditor'

const {
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
  fetchNeighbors,
  openEntityDrawer,
  saveEntityChanges,
  deleteEntity,
  handleUnlink,
  handleUpdateEdgeProp,
  confirmCreateNode,
  searchNodes,
  confirmBind
} = useGraphEditor()
const graphCanvasRef = ref<any>(null)

const handleLocateNode = (uuid: string) => {
  drawerVisible.value = false
  setTimeout(() => {
    graphCanvasRef.value?.locateNode(uuid)
  }, 200)
}

const filteredGraphData = computed(() => {
  const filteredNodes = rawGraphData.value.nodes.filter(n => selectedTypes.value.includes(n.nodeType || ''))
  const validNodeIds = new Set(filteredNodes.map(n => n.id))
  const filteredEdges = rawGraphData.value.edges.filter(e => validNodeIds.has(e.source) && validNodeIds.has(e.target))
  return { nodes: filteredNodes, edges: filteredEdges }
})

onMounted(() => {
  fetchGraphData('initial')
})
</script>

<style scoped>
.entity-editor-container {
  height: calc(100vh - 120px);
}
</style>
