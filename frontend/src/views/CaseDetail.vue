<template>
  <div class="case-detail">
    <!-- 顶部时间线 -->
    <div class="timeline-bar">
      <span
        @click="timelineOpen = !timelineOpen"
        style="cursor:pointer;user-select: none;"
      >
        ⏳ 时间线 {{ timelineOpen ? '▲' : '▼' }}
      </span>
      <button v-if="timelineOpen" @click="showAddEvent = !showAddEvent">
        {{ showAddEvent ? '取消' : '添加事件' }}
      </button>
    </div>

    <!-- 时间线内容区（标签模式） -->
    <div v-if="timelineOpen" class="timeline-content">
      <div v-if="showAddEvent" class="add-event-form">
        <input v-model="newEventTime" placeholder="时间，如 案发当晚20:00" />
        <input v-model="newEventDesc" placeholder="事件描述" @keyup.enter="addTimelineEvent" />
        <button @click="addTimelineEvent" :disabled="!newEventTime.trim() || !newEventDesc.trim()">
          添加
        </button>
      </div>

      <div v-if="timelineEvents.length" class="event-list">
        <div v-for="event in timelineEvents" :key="event.id" class="event-item">
          <button class="move-btn" @click="moveEvent(event.id, 'up')" title="上移">▲</button>
          <button class="move-btn" @click="moveEvent(event.id, 'down')" title="下移">▼</button>
          <span class="event-time">{{ event.event_time }}</span>
          <span class="event-desc">{{ event.description }}</span>
          <button class="delete-event-btn" @click="handleDeleteEvent(event.id)">✕</button>
        </div>
      </div>
      <p v-else class="empty-hint">暂无时间线事件，点击上方按钮添加</p>
    </div>

    <!-- 主区域 -->
    <div class="main-area">
      <!-- 便签墙画布 -->
      <div class="canvas-area">
        <VueFlow
          ref="vueFlowRef"
          v-model:nodes="nodes"
          v-model:edges="edges"
          :node-types="nodeTypes"
          @nodes-change="onNodesChange"
          @edges-change="onEdgesChange"
          @connect="onConnect"
          @node-click="selectNode"
          @pane-click="deselectNode"
          :default-viewport="{ zoom: 1, x: 0, y: 0 }"
          fit-view-on-init
        >
        </VueFlow>
        <button class="center-btn" @click="goToCenter" title="回到中心">🏠</button>
        <!-- 添加便签按钮 -->
        <div class="add-note-bar">
          <button @click="addNote('clue')">+ 添加线索</button>
          <button @click="addNote('suspect')">+ 添加嫌疑人</button>
        </div>
      </div>

      <!-- 右侧面板 -->
      <div class="side-panel" :class="{ collapsed: !panelOpen }">
        <div class="panel-header">
          <button class="toggle-panel-btn" @click="panelOpen = !panelOpen">
            {{ panelOpen ? '▶' : '◀' }}
          </button>
          <h3 v-show="panelOpen">工具面板</h3>
        </div>

        <div v-show="panelOpen" class="panel-content">
          <div v-if="selectedNode">
            <p><strong>编辑便签</strong></p>
            <textarea v-model="selectedNode.data.content" rows="4" style="width:100%"></textarea>
            <div class="color-picker">
              <div
                v-for="c in presetColors"
                :key="c"
                class="color-swatch"
                :style="{ background: c }"
                :class="{ active: selectedNode.data.color === c }"
                @click="selectedNode.data.color = c"
              ></div>
            </div>
            <button @click="saveSelectedNode">保存</button>
            <button @click="deleteSelectedNode">删除</button>
          </div>
          <p v-else>点击便签进行编辑</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { VueFlow } from '@vue-flow/core'
import NoteNode from '@/components/NoteNode.vue'
import {
  getNotes, createNote, updateNote, deleteNote,
  getConnections, createConnection,
  getTimelineEvents, createTimelineEvent,
  deleteTimelineEvent as deleteTimelineEventApi,
  moveTimelineEvent,
} from '@/api/index'

import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'

const props = defineProps<{ id: string }>()
const caseId = Number(props.id)

const panelOpen = ref(true)
const nodeTypes: Record<string, any> = { note: NoteNode }

const nodes = ref<any[]>([])
const edges = ref<any[]>([])
const selectedNode = ref<any | null>(null)
const vueFlowRef = ref<any>(null)

const presetColors = [
  '#FFF9C4', '#FFCCBC', '#C8E6C9', '#BBDEFB',
  '#E1BEE7', '#FFE0B2', '#B2EBF2', '#F5F5F5',
]
const centerPoint = { x: 400, y: 300 }

// 时间线状态
const timelineOpen = ref(false)
const showAddEvent = ref(false)
const timelineEvents = ref<any[]>([])
const newEventTime = ref('')
const newEventDesc = ref('')

function goToCenter() {
  vueFlowRef.value?.setCenter(centerPoint.x, centerPoint.y, { zoom: 1 })
}

onMounted(async () => {
  await loadNotes()
  await loadConnections()
  await loadTimelineEvents()
  await nextTick()
  goToCenter()
})

async function loadNotes() {
  try {
    const res = await getNotes(caseId)
    nodes.value = res.data.map((n: any) => ({
      id: String(n.id),
      type: 'note',
      position: { x: n.pos_x, y: n.pos_y },
      data: { content: n.content, type: n.type, color: n.color },
      style: { width: `${n.width}px`, height: `${n.height}px` },
    }))
  } catch (err) {
    console.error('加载便签失败', err)
  }
}

async function loadConnections() {
  try {
    const res = await getConnections(caseId)
    edges.value = res.data.map((c: any) => ({
      id: String(c.id),
      source: String(c.from_note_id),
      target: String(c.to_note_id),
      label: c.label,
    }))
  } catch (err) {
    console.error('加载连线失败', err)
  }
}

async function loadTimelineEvents() {
  try {
    const res = await getTimelineEvents(caseId)
    timelineEvents.value = res.data
  } catch (err) {
    console.error('加载时间线失败', err)
  }
}

async function addNote(type: string) {
  const colors: Record<string, string> = { clue: '#FFF9C4', suspect: '#FFCCBC' }
  try {
    const res = await createNote(caseId, {
      type,
      content: type === 'clue' ? '新线索' : '新嫌疑人',
      color: colors[type],
      pos_x: Math.random() * 400,
      pos_y: Math.random() * 300,
      width: 200,
      height: 120,
    })
    nodes.value.push({
      id: String(res.data.id),
      type: 'note',
      position: { x: res.data.pos_x, y: res.data.pos_y },
      data: { content: res.data.content, type: res.data.type, color: res.data.color },
      style: { width: `${res.data.width}px`, height: `${res.data.height}px` },
    })
  } catch (err) {
    console.error('创建便签失败', err)
  }
}

async function onConnect(connection: any) {
  const { source, target, sourceHandle, targetHandle } = connection
  if (edges.value.some((e: any) =>
    e.source === source && e.target === target &&
    e.sourceHandle === sourceHandle && e.targetHandle === targetHandle
  )) return

  try {
    const res = await createConnection(caseId, {
      from_note_id: Number(source),
      to_note_id: Number(target),
      label: '',
    })
    edges.value.push({
      id: String(res.data.id),
      source,
      target,
      sourceHandle: sourceHandle ?? undefined,
      targetHandle: targetHandle ?? undefined,
      label: '',
    })
  } catch (err) {
    console.error('创建连线失败', err)
  }
}

async function onNodesChange(changes: any[]) {
  for (const change of changes) {
    if (change.type === 'position' && change.position) {
      await updateNote(caseId, Number(change.id), {
        pos_x: change.position.x,
        pos_y: change.position.y,
      })
    }
    if (change.type === 'dimensions' && change.dimensions) {
      await updateNote(caseId, Number(change.id), {
        width: change.dimensions.width,
        height: change.dimensions.height,
      })
    }
  }
}

function onEdgesChange() {}

function selectNode({ node }: { node: any }) {
  selectedNode.value = node
}

function deselectNode() {
  selectedNode.value = null
}

async function saveSelectedNode() {
  if (!selectedNode.value) return
  try {
    await updateNote(caseId, Number(selectedNode.value.id), {
      content: selectedNode.value.data.content,
      type: selectedNode.value.data.type,
      color: selectedNode.value.data.color,
    })
    alert('保存成功')
  } catch (err) {
    console.error('保存便签失败', err)
  }
}

async function deleteSelectedNode() {
  if (!selectedNode.value) return
  if (!confirm('确认删除这个便签？关联的连线也会一并删除。')) return
  try {
    await deleteNote(caseId, Number(selectedNode.value.id))
    edges.value = edges.value.filter((e: any) => e.source !== selectedNode.value.id && e.target !== selectedNode.value.id)
    nodes.value = nodes.value.filter((n: any) => n.id !== selectedNode.value.id)
    selectedNode.value = null
  } catch (err) {
    console.error('删除便签失败', err)
  }
}

async function addTimelineEvent() {
  if (!newEventTime.value.trim() || !newEventDesc.value.trim()) return
  try {
    await createTimelineEvent(caseId, {
      event_time: newEventTime.value.trim(),
      description: newEventDesc.value.trim(),
      source: 'manual',
    })
    newEventTime.value = ''
    newEventDesc.value = ''
    showAddEvent.value = false
    await loadTimelineEvents()
  } catch (err) {
    console.error('添加时间线事件失败', err)
  }
}

async function moveEvent(eventId: number, direction: string) {
  try {
    await moveTimelineEvent(caseId, eventId, direction)
    await loadTimelineEvents()
  } catch (err) {
    console.error('移动事件失败', err)
  }
}

async function handleDeleteEvent(eventId: number) {
  try {
    await deleteTimelineEventApi(caseId, eventId)
    await loadTimelineEvents()
  } catch (err) {
    console.error('删除事件失败', err)
  }
}
</script>

<style scoped>
.case-detail {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 时间线顶栏 */
.timeline-bar {
  height: 40px;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  border-bottom: 1px solid #ccc;
  flex-shrink: 0;
}

/* 时间线内容 */
.timeline-content {
  max-height: 200px;
  overflow-y: auto;
  border-bottom: 1px solid #ccc;
  background: #fafafa;
  padding: 8px 16px;
}
.add-event-form {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}
.add-event-form input {
  flex: 1;
  min-width: 120px;
  padding: 4px 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
}
.add-event-form button {
  padding: 4px 12px;
  background: #e8f5e9;
  border: 1px solid #ccc;
  border-radius: 4px;
  cursor: pointer;
}
.event-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.event-item {
  display: flex;
  align-items: center;
  gap: 8px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 13px;
}
.event-time {
  font-weight: bold;
  color: #555;
  white-space: nowrap;
}
.event-desc {
  color: #333;
}
.move-btn {
  background: none;
  border: 1px solid #ddd;
  border-radius: 2px;
  font-size: 10px;
  padding: 0 2px;
  cursor: pointer;
  color: #888;
  line-height: 1;
}
.move-btn:hover {
  color: #333;
  border-color: #999;
}
.delete-event-btn {
  background: none;
  border: none;
  color: #c62828;
  cursor: pointer;
  font-size: 14px;
  padding: 0 2px;
}
.empty-hint {
  color: #999;
  text-align: center;
  font-size: 13px;
}

/* 主区域 */
.main-area {
  flex: 1;
  display: flex;
  overflow: hidden;
}
.canvas-area {
  flex: 1;
  position: relative;
}
.add-note-bar {
  position: absolute;
  bottom: 20px;
  left: 20px;
  z-index: 10;
  display: flex;
  gap: 8px;
}
.add-note-bar button {
  padding: 6px 12px;
  background: #fff;
  border: 1px solid #ccc;
  border-radius: 4px;
  cursor: pointer;
}
.add-note-bar button:hover {
  background: #f5f5f5;
}

/* 回到中心按钮 */
.center-btn {
  position: absolute;
  bottom: 20px;
  right: 20px;
  z-index: 10;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 1px solid #ccc;
  background: white;
  font-size: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  transition: background 0.2s;
}
.center-btn:hover {
  background: #f0f0f0;
}

/* 右侧面板 */
.side-panel {
  width: 300px;
  border-left: 1px solid #ccc;
  background: #fff;
  overflow-y: auto;
  position: relative;
  transition: width 0.3s;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
}
.side-panel.collapsed {
  width: 40px;
  overflow: hidden;
}
.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-bottom: 1px solid #eee;
  flex-shrink: 0;
}
.toggle-panel-btn {
  background: #fff;
  border: 1px solid #ccc;
  border-radius: 4px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 14px;
  padding: 0;
  flex-shrink: 0;
}
.toggle-panel-btn:hover {
  background: #f0f0f0;
}
.panel-header h3 {
  margin: 0;
  white-space: nowrap;
}
.panel-content {
  padding: 12px;
  flex: 1;
  overflow-y: auto;
}

/* 编辑区 */
textarea {
  resize: none;
  width: 100%;
  min-height: 80px;
}
.color-picker {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 8px 0;
}
.color-swatch {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 2px solid transparent;
  cursor: pointer;
  transition: border-color 0.2s;
}
.color-swatch.active {
  border-color: #333;
}
.color-swatch:hover {
  border-color: #999;
}
</style>