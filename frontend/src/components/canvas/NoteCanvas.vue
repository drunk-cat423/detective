<template>
  <div class="canvas-area">
    <VueFlow
      ref="vueFlowRef"
      v-model:nodes="nodes"
      v-model:edges="edges"
      :node-types="nodeTypes"
      @nodes-change="onNodesChange"
      @connect="onConnect"
      @node-click="selectNode"
      @pane-click="deselectNode"
      @edge-double-click="onEdgeDoubleClick"
      :default-viewport="{ zoom: 1, x: 0, y: 0 }"
      fit-view-on-init
      :default-edge-options="defaultEdgeOptions"
    />

    <div
      v-if="editingEdgeForLabel"
      class="edge-edit-toolbar"
      :style="{ left: editEdgePosition.x + 'px', top: editEdgePosition.y + 'px' }"
      @click.stop
    >
      <div class="edge-edit-input-wrapper">
        <input
          ref="edgeEditInput"
          :value="editEdgeLabelText"
          type="text"
          placeholder="输入备注..."
          @keyup.enter="saveEdgeLabelEdit"
          @blur="saveEdgeLabelEdit"
          @click.stop
          autofocus
          @input="emit('update:editEdgeLabelText', ($event.target as HTMLInputElement).value)"
        />
      </div>
      <button class="edge-delete-btn" @mousedown.stop.prevent="deleteCurrentEdge" title="删除连线">
        🗑️
      </button>
    </div>

    <button class="center-btn" @click="goToCenter" title="回到中心">
      <img src="/home.png" alt="回到中心" class="center-icon" />
    </button>

    <div class="add-note-bar">
      <button @click="$emit('add-note', 'clue')">添加线索</button>
      <button @click="$emit('add-note', 'suspect')">添加嫌疑人</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { VueFlow } from '@vue-flow/core'
import type { NodeTypesObject } from '@vue-flow/core'
import NoteNode from '@/components/NoteNode.vue'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'

const props = defineProps<{
  nodes: any[]
  edges: any[]
  editingEdgeForLabel: any
  editEdgeLabelText: string
  editEdgePosition: { x: number; y: number }
  defaultEdgeOptions: any
}>()

const emit = defineEmits<{
  'update:nodes': [nodes: any[]]
  'update:edges': [edges: any[]]
  'update:editEdgeLabelText': [value: string]
  'select-node': [node: any]
  'deselect-node': []
  'go-to-center': [vueFlowRef: any]
  'on-connect': [connection: any]
  'on-nodes-change': [changes: any[]]
  'on-edge-double-click': [params: any]
  'save-edge-label-edit': []
  'delete-current-edge': []
  'add-note': [type: string]
}>()

const vueFlowRef = ref<any>(null)

const nodeTypes = { note: NoteNode } as NodeTypesObject

const nodes = computed({
  get: () => props.nodes,
  set: (v) => emit('update:nodes', v)
})

const edges = computed({
  get: () => props.edges,
  set: (v) => emit('update:edges', v)
})

function selectNode(params: any) { emit('select-node', params.node) }
function deselectNode() { emit('deselect-node') }
function goToCenter() { emit('go-to-center', vueFlowRef.value) }
function onConnect(connection: any) { emit('on-connect', connection) }
function onNodesChange(changes: any[]) { emit('on-nodes-change', changes) }
function onEdgeDoubleClick(params: any) { emit('on-edge-double-click', params) }
function saveEdgeLabelEdit() { emit('save-edge-label-edit') }
function deleteCurrentEdge() { emit('delete-current-edge') }
</script>

<style scoped>
.canvas-area {
  flex: 1;
  position: relative;
  background:
    radial-gradient(circle at 20% 80%, rgba(212, 168, 67, 0.03) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(58, 123, 200, 0.03) 0%, transparent 50%),
    #fdf1a3;
}

.add-note-bar {
  position: absolute;
  bottom: 24px;
  left: 24px;
  z-index: 10;
  display: flex;
  gap: 12px;
}

.add-note-bar button {
  padding: 10px 20px;
  background: #fff;
  border: 2px solid #fff;
  border-radius: 20px;
  color: var(--gold-deep);
  font-weight: 600;
  cursor: pointer;
  font-size: 13px;
  box-shadow: var(--shadow);
  transition: all 0.3s;
}

.add-note-bar button:hover {
  color: var(--white);
  border-color: #fff;
  transform: translateY(-2px);
  box-shadow: var(--shadow-hover);
}

.center-btn {
  position: absolute;
  bottom: 24px;
  right: 24px;
  z-index: 10;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: 2px solid var(--gold);
  background: var(--white);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: var(--shadow);
  transition: all 0.3s;
  line-height: 0;
  padding: 0;
}

.center-btn:hover {
  background: var(--gold);
  transform: scale(1.1) rotate(-10deg);
  box-shadow: var(--shadow-hover);
}

.center-icon {
  width: 28px;
  height: 28px;
  display: block;
  color: #333;
}

.edge-edit-toolbar {
  position: fixed;
  transform: translate(-50%, -50%);
  z-index: 1000;
  display: flex;
  gap: 10px;
  align-items: center;
  background: transparent;
}

.edge-edit-input-wrapper {
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(4px);
  border-radius: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 2px solid var(--gold);
  padding: 4px 12px;
}

.edge-edit-input-wrapper input {
  border: none;
  background: transparent;
  outline: none;
  font-size: 16px;
  padding: 6px 0;
  min-width: 120px;
  text-align: center;
  color: var(--text);
}

.edge-delete-btn {
  background: white;
  border: 1px solid #ddd;
  border-radius: 50%;
  width: 34px;
  height: 34px;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  transition: all 0.2s;
  padding: 0;
  flex-shrink: 0;
}

.edge-delete-btn:hover {
  background: #ffebee;
  border-color: #c62828;
  color: #c62828;
  transform: scale(1.05);
}
</style>
