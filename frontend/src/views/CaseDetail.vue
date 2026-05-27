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

    <!-- 时间线内容区（时间轴模式） -->
    <div v-if="timelineOpen" class="timeline-panel">
      <!-- 添加表单 -->
      <div class="timeline-form">
        <div class="datetime-picker">
          <input type="number" v-model="eventYear" placeholder="年" min="1" max="99999" />
          <span>-</span>
          <input type="number" v-model="eventMonth" placeholder="月" min="1" max="12" />
          <span>-</span>
          <input type="number" v-model="eventDay" placeholder="日" min="1" max="31" />
          <span>&nbsp;</span>
          <input type="number" v-model="eventHour" placeholder="时" min="0" max="23" />
          <span>:</span>
          <input type="number" v-model="eventMinute" placeholder="分" min="0" max="59" />
        </div>
        <input v-model="newEventDesc" placeholder="事件描述" @keyup.enter="addTimelineEvent" />
        <button @click="addTimelineEvent">添加</button>
      </div>

      <!-- 时间轴 -->
      <div class="timeline-axis" ref="timelineAxis" @click="closeAllPopups">
        <div class="axis-line"></div>
        
        <div
          v-for="(event, idx) in sortedEvents"
          :key="event.id"
          class="timeline-dot-wrapper"
          :style="{ left: getDotPosition(event, sortedEvents) + '%' }"
        >
          <div
            class="timeline-dot"
            @mouseenter="showPopup(event)"
            @mouseleave="onDotMouseLeave(event)"
            @click.stop="lockPopup(event)"
          >
            <div class="dot"></div>
            <span class="dot-time">{{ formatEventTime(event.event_time) }}</span>
          </div>

          <!-- 悬停/锁定弹出详情 -->
          <div
            v-if="hoveredEvent?.id === event.id || lockedEvents.has(event.id)"
            class="event-popup"
            :class="{ 'popup-left': getDotPosition(event, sortedEvents) < 20, 'popup-right': getDotPosition(event, sortedEvents) > 80 }"
            @mouseenter="onPopupMouseEnter(event)"
            @mouseleave="onPopupMouseLeave(event)"
            @click.stop
          >
            <div class="popup-header">
              <strong>{{ event.event_time }}</strong>
              <button class="popup-close-btn" @click="closePopup(event)">✕</button>
            </div>
            <p>{{ event.description }}</p>
            <button class="popup-delete-btn" @click="handleDeleteEvent(event.id)">删除事件</button>
          </div>
        </div>
      </div>
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
import { ref, onMounted, nextTick ,computed} from 'vue'
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

// 添加表单
const eventYear = ref(new Date().getFullYear())
const eventMonth = ref(1)
const eventDay = ref(1)
const eventHour = ref(0)
const eventMinute = ref(0)
const newEventDesc = ref('')

// 弹出框状态
const hoveredEvent = ref<any>(null)
const lockedEvents = ref<Set<number>>(new Set())  // 用 Set 存 id，支持多个同时锁定的事件（点击后）

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


// 排序
const sortedEvents = computed(() => {
  return [...timelineEvents.value].sort((a, b) => a.event_time.localeCompare(b.event_time))
})

function formatEventTime(eventTime: string) {
  if (!eventTime) return ''
  const match = eventTime.match(/(\d+)年(\d+)月(\d+)日/)
  if (match) {
    return `${match[2]}/${match[3]}`
  }
  return eventTime
}

function getDotPosition(event: any, events: any[]) {
  if (events.length <= 1) return 50
  const sorted = [...events].sort((a, b) => a.event_time.localeCompare(b.event_time))
  const firstTime = parseEventTime(sorted[0].event_time)
  const lastTime = parseEventTime(sorted[sorted.length - 1].event_time)
  const range = lastTime - firstTime || 1
  const eventTime = parseEventTime(event.event_time)
  return ((eventTime - firstTime) / range) * 100
}

function parseEventTime(str: string): number {
  const match = str.match(/(\d+)年(\d+)月(\d+)日\s(\d+):(\d+)/)
  if (!match) return 0
  return new Date(+match[1], +match[2] - 1, +match[3], +match[4], +match[5]).getTime()
}


// 弹出框控制
function showPopup(event: any) {
  if (!lockedEvents.value.has(event.id)) {
    hoveredEvent.value = event
  }
}

function onDotMouseLeave(event: any) {
  if (!lockedEvents.value.has(event.id)) {
    hoveredEvent.value = null
  }
}

function onPopupMouseEnter(event: any) {
  hoveredEvent.value = event
}

function onPopupMouseLeave(event: any) {
  if (!lockedEvents.value.has(event.id)) {
    hoveredEvent.value = null
  }
}

function lockPopup(event: any) {
  const newSet = new Set(lockedEvents.value)
  if (newSet.has(event.id)) {
    newSet.delete(event.id)
  } else {
    newSet.add(event.id)
  }
  lockedEvents.value = newSet
  hoveredEvent.value = event
}

function closePopup(event: any) {
  const newSet = new Set(lockedEvents.value)
  newSet.delete(event.id)
  lockedEvents.value = newSet
  hoveredEvent.value = null
}

function closeAllPopups() {
  lockedEvents.value = new Set()
  hoveredEvent.value = null
}




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
  if (!newEventDesc.value.trim()) return
  const eventTimeStr = `${eventYear.value}年${eventMonth.value}月${eventDay.value}日 ${String(eventHour.value).padStart(2, '0')}:${String(eventMinute.value).padStart(2, '0')}`
  
  try {
    await createTimelineEvent(caseId, {
      event_time: eventTimeStr,
      description: newEventDesc.value.trim(),
      source: 'manual',
    })
    newEventDesc.value = ''
    showAddEvent.value = false
    await loadTimelineEvents()
  } catch (err) {
    console.error('添加时间线事件失败', err)
  }
}

async function handleDeleteEvent(eventId: number) {
  try {
    await deleteTimelineEventApi(caseId, eventId)
    const newSet = new Set(lockedEvents.value)
    newSet.delete(eventId)
    lockedEvents.value = newSet
    hoveredEvent.value = null
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

/* 时间线面板 */
.timeline-panel {
  background: #fafafa;
  border-bottom: 1px solid #ddd;
  padding: 8px 20px;
  max-height: 140px;
  overflow: visible;
}
.timeline-form {
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
  flex-wrap: wrap;
  align-items: center;
}
.datetime-picker {
  display: flex;
  gap: 1px;
  align-items: center;
  font-size: 13px;
}
.datetime-picker input {
  width: 52px;
  padding: 2px 4px;
  border: 1px solid #ccc;
  border-radius: 3px;
  text-align: center;
  font-size: 13px;
}
.timeline-form input[type="text"] {
  flex: 1;
  min-width: 120px;
  padding: 2px 6px;
  border: 1px solid #ccc;
  border-radius: 3px;
  font-size: 13px;
}
.timeline-form button {
  padding: 2px 12px;
  background: #e8f5e9;
  border: 1px solid #ccc;
  border-radius: 3px;
  cursor: pointer;
  font-size: 13px;
}

/* 时间轴 */
.timeline-axis {
  position: relative;
  height: 50px;
  margin: 0 30px;
}
.axis-line {
  position: absolute;
  top: 20px;
  left: 0;
  right: 0;
  height: 2px;
  background: #bbb;
}
.timeline-dot-wrapper {
  position: absolute;
  top: 12px;
  transform: translateX(-50%);
  text-align: center;
  z-index: 2;
}
.timeline-dot {
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.dot {
  width: 12px;
  height: 12px;
  background: #555;
  border-radius: 50%;
  border: 2px solid white;
  box-shadow: 0 0 0 1px #555;
  transition: transform 0.2s, background 0.2s;
}
.dot:hover {
  transform: scale(1.3);
  background: #333;
}
.dot-time {
  font-size: 9px;
  color: #888;
  margin-top: 2px;
  white-space: nowrap;
}

/* 弹出详情框（在圆点下方） */
.event-popup {
  position: absolute;
  top: 30px;
  left: 50%;
  transform: translateX(-50%);
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 8px 12px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.18);
  width: 200px;
  z-index: 30;
  pointer-events: auto;
}
.popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.popup-header strong {
  font-size: 12px;
  color: #333;
}
.popup-close-btn {
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  font-size: 14px;
  padding: 0;
  line-height: 1;
}
.popup-close-btn:hover {
  color: #333;
}
.event-popup p {
  margin: 4px 0;
  font-size: 12px;
  color: #555;
}
.popup-delete-btn {
  margin-top: 4px;
  padding: 2px 10px;
  background: #ffebee;
  border: 1px solid #e0c0c0;
  border-radius: 4px;
  color: #c62828;
  cursor: pointer;
  font-size: 12px;
}
.popup-delete-btn:hover {
  background: #ffcdd2;
}

/* 弹出详情框（在圆点下方） */
.event-popup {
  position: absolute;
  top: 30px;
  left: 50%;
  transform: translateX(-50%);
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 8px 12px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.18);
  width: 200px;
  z-index: 30;
  pointer-events: auto;
}
/* 左侧：靠左对齐 */
.event-popup.popup-left {
  left: 0;
  transform: translateX(0);
}
/* 右侧：靠右对齐 */
.event-popup.popup-right {
  left: auto;
  right: 0;
  transform: translateX(0);
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