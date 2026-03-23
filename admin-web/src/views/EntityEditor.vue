<template>
  <div class="entity-editor-container">
    <GraphCanvas
      :data="filteredGraphData"
      :loading="loading"
      :available-types="availableTypes"
      v-model:selected-types="selectedTypes"
      @node-click="openEntityDrawer"
      @refresh="fetchGraphData"
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
import { computed, onMounted } from 'vue'
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
  openEntityDrawer,
  saveEntityChanges,
  deleteEntity,
  handleUnlink,
  handleUpdateEdgeProp,
  confirmCreateNode,
  searchNodes,
  confirmBind
} = useGraphEditor()

const filteredGraphData = computed(() => {
  const filteredNodes = rawGraphData.value.nodes.filter(n => selectedTypes.value.includes(n.nodeType || ''))
  const validNodeIds = new Set(filteredNodes.map(n => n.id))
  const filteredEdges = rawGraphData.value.edges.filter(e => validNodeIds.has(e.source) && validNodeIds.has(e.target))
  return { nodes: filteredNodes, edges: filteredEdges }
})

onMounted(() => {
  fetchGraphData()
})
</script>

<style scoped>
.entity-editor-container {
  height: calc(100vh - 120px);
}
</style>
