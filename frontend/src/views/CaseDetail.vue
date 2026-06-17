<template>
  <div class="case-detail">

    <!-- 顶部时间线 -->
    <div class="timeline-bar">
      <div style="display:flex; align-items:center; gap:12px;">
        <router-link to="/" class="back-btn">🏠︎</router-link>
        <span @click="timelineOpen = !timelineOpen" class="timeline-toggle">
          ⏳ 时间线 {{ timelineOpen ? '▲' : '▼' }}
        </span>
      </div>
      <button v-if="timelineOpen" @click="showAddEvent = !showAddEvent">
        {{ showAddEvent ? '取消' : '+ 添加事件' }}
      </button>
    </div>


    <!-- 时间线内容区（时间轴模式） -->
    <div v-if="timelineOpen" class="timeline-panel">
      <!-- 添加表单 -->
      <div v-if= "showAddEvent"class="timeline-form">
        <div class="datetime-picker">
          <input type="number" v-model="eventYear" placeholder="年" min="1" @change="fixDate" />
          <span>-</span>
          <input type="number" v-model="eventMonth" placeholder="月" min="1" max="12" @change="fixDate" />
          <span>-</span>
          <input type="number" v-model="eventDay" placeholder="日" min="1" max="31" @change="fixDate" />
          <span>&nbsp;</span>
          <input type="number" v-model="eventHour" placeholder="时" min="0" max="23" @change="fixTime" />
          <span>:</span>
          <input type="number" v-model="eventMinute" placeholder="分" min="0" max="59" @change="fixTime" />
        </div>
        <input type ="text" v-model="newEventDesc" placeholder="事件描述" @keyup.enter="addTimelineEvent" />
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
          @edge-double-click = "onEdgeDoubleClick"
          :default-edge-options="defaultEdgeOptions"

        >
      </VueFlow>
        <!-- 连线备注浮动工具栏 -->
        <div v-if="editingEdgeForLabel" class="edge-edit-toolbar" :style="{ left: editEdgePosition.x + 'px', top: editEdgePosition.y + 'px' }" @click.stop>
          <div class="edge-edit-input-wrapper">
            <input
              ref="edgeEditInput"
              v-model="editEdgeLabelText"
              type="text"
              placeholder="输入备注..."
              @keyup.enter="saveEdgeLabelEdit"
              @blur="saveEdgeLabelEdit"
              @click.stop
              autofocus
            />
          </div>
          <button class="edge-delete-btn" @mousedown.stop.prevent="deleteCurrentEdge" title="删除连线">🗑️</button>
        </div>
        <button class="center-btn" @click="goToCenter" title="回到中心">
          <img src="/home.png" alt="回到中心" class="center-icon" />
        </button>
        <!-- 添加便签按钮 -->
        <div class="add-note-bar">
          <button @click="addNote('clue')"> 添加线索 </button>
          <button @click="addNote('suspect')"> 添加嫌疑人 </button>
        </div>
      </div>

      <!-- 右侧面板 -->
      <div class="side-panel" :class="{ collapsed: !panelOpen }">
        <div class="panel-header">
          <button class="toggle-panel-btn" @click="panelOpen = !panelOpen">
            {{ panelOpen ? '▶' : '◀' }}
          </button>
          <div v-show="panelOpen" class="tab-buttons">
            <button
              :class="{ active: activeTab === 'edit' }"
              @click="activeTab = 'edit'"
            >编辑</button>
            <button
              :class="{ active: activeTab === 'chat' }"
              @click="activeTab = 'chat'"
            >对话</button>
            <button
            :class ="{ active: activeTab === 'docs'}"
            @click = "activeTab ='docs'"
            >文档</button>
            <button
            :class ="{ active: activeTab === 'info'}"
            @click = "activeTab ='info'"
            >已知信息</button>
          </div>
        </div>

        <!-- 编辑 Tab -->
        <div v-show="panelOpen && activeTab === 'edit'" class="panel-content">
          <div v-if="selectedNode">
            <div v-if="selectedNode.data.type === 'suspect'" class="edit-field">
            <label>嫌疑人名字</label>
            <input
              v-model="selectedNode.data.name"
              placeholder="请输入名字"
              class = "suspect-name-input"
            />
            </div>
            <p><strong>编辑便签</strong></p>
            <textarea v-model="selectedNode.data.content" rows="4"></textarea>
            
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
            <button class = "edit-btn save-btn" @click="saveSelectedNode">保存</button>
            <button class = "edit-btn delete-btn" @click="deleteSelectedNode">删除</button>
          </div>
          <p v-else>点击便签进行编辑</p>
        </div>


        <!-- 对话 Tab -->
        <div v-show="panelOpen && activeTab === 'chat'" class="panel-content chat-panel">
          <div class="chat-messages" ref="chatMessages">
            <div v-if="chatHistory.length === 0" class="chat-empty">
              💬 和助手小姐聊聊吧
            </div>
            <div
              v-for="(msg, idx) in chatHistory"
              :key="idx"
              :class="['chat-msg', msg.role]"
            >
              <img
                :src="msg.role === 'user' ? userAvatar : agentAvatar"
                :class="['avatar', msg.role]"
              />
              <!-- 用户消息：纯文本 -->
              <div v-if="msg.role === 'user'" class="msg-bubble">{{ msg.content }}</div>
              
              <!-- Agent 消息：Markdown 渲染 -->
              <div v-else class = "msg-bubble">
                <template v-if = "msg.content">
                  <div v-html="renderMarkdown(msg.content)"></div>
                </template>
                <template v-else-if = "isThinking">
                  <span class = "thinking-text">
                    小识正在努力思考
                    <span class = "thinking-dots">...</span>
                  </span>
                </template>
              </div>
            </div>
          </div>
          <div class="chat-input">
            <input
              ref = "chatInputRef"
              v-model="chatInput"
              placeholder="输入消息..."
              @keydown.enter = "handleEnterKey"
              :disabled="chatLoading"
            />
            <button @click="sendMessage" :disabled="chatLoading || !chatInput.trim()">发送</button>
            <button @click="clearScreen" :disabled="chatHistory.length === 0">清屏</button>
            <button @click="resetMemory" :disabled="chatHistory.length === 0" class="reset-btn">重置</button>
          </div>
        </div>

        <!-- 文档 Tab  -->
         <div v-show ="panelOpen && activeTab === 'docs'" class = "panel-content">
          <div class = "upload-area"
              @dragover.prevent
              @drop.prevent = "handleDrop"
              @click = "triggerFileInput">
              <input type="file" ref = "fileInput" accept = ".txt" style = "display: none" @change = "handleFileSelect"/>
              <p>📂 拖拽或点击上传</p>
              <p style = "font-size:12px;color:#999;">支持utf-8编码</p>
          </div>
          <div v-if ="uploading" class = "upload-progress">上传中...</div>
          <div v-if ="docList.length >0" class = "doc-list">
            <h4>已上传文档</h4>
            <ul>
              <li v-for = "doc in docList" :key = "doc.id">
                {{ doc.filename }} 
              </li>
            </ul>
          </div>

         </div>

        <!-- 已知信息tab -->
        <div v-show = "panelOpen && activeTab === 'info'" class ="panel-content">
          <div class ="known-info-form">
            <textarea v-model ="newInfoContent"
            placeholder="请输入信息"
            rows ="3">
            </textarea>
          </div>
          <div>
            <button class ="known-info-button" @click ="addKnownInfo" :disabled="!newInfoContent.trim()">添加</button>
          </div>
          <div class="info-hint">💡 提示：双击列表中的信息可直接编辑</div>
          <div v-if ="getKnownInfos.length ===0" class ="empty-info">
            暂无已知信息
          </div>
          <ul v-else class ="known-info-list">
            <li v-for="info in knownInfos" :key="info.id">
              <span 
                @dblclick.prevent ="startEditInfo(info)" 
                class="info-content"
                :class="{ editing: editingId === info.id }"
              >
                <template v-if="editingId === info.id">
                  <textarea 
                    v-model="editInfoContent" 
                    rows="2" 
                    @blur="saveEditInfo(info)" 
                    @keyup.enter="saveEditInfo(info)"
                    :ref = "(el:any) => {if (el) editTextareaRefs[info.id] = el}"
                  ></textarea>
                </template>
                <template v-else>
                  {{ info.content }}
                </template>
              </span>
              <div class ="info-actions">
                <button @click ="deleteKnownInfoItem(info.id)" class = "delete-btn">🗑️</button>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick ,computed, watch,reactive} from 'vue'
import { VueFlow} from '@vue-flow/core'
import NoteNode from '@/components/NoteNode.vue'
import {
  getNotes, createNote, updateNote, deleteNote,
  getConnections, createConnection,
  getTimelineEvents, createTimelineEvent,updateConnection,deleteConnection,
  deleteTimelineEvent as deleteTimelineEventApi
} from '@/api/index'

import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import { getAgentHistory, clearAgentHistory } from '@/api/index'
import { marked } from 'marked'
import DOMPurify  from 'dompurify'
import { uploadDocument,getDocument } from '@/api/index'
import { getKnownInfos,createKnownInfo,updateKnownInfo,deleteKnownInfo } from '@/api/index'


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

// 添加时间线表单
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

// 侧边栏 Tab
const activeTab = ref<'edit' | 'chat' | 'docs' |'info'>('edit')

// 对话相关
const chatHistory = ref<{ role: string; content: string }[]>([])
const chatInput = ref('')
const chatLoading = ref(false)
const chatMessages = ref<HTMLElement | null>(null)
const chatInputRef = ref<HTMLInputElement | null>(null)
const isThinking = ref(false)


//用户头像
const userAvatar = ref('/avatar-user.png')
//agent头像
const agentAvatar = ref('/avatar-agent.png')

//文档上传相关
const fileInput = ref<HTMLInputElement | null>(null)
const uploading = ref<any>(false)
const docList = ref<any[]>([])

//已知信息相关
const knownInfos = ref<any[]>([])
const newInfoContent = ref('')
const editingId = ref<number | null>(null)
const editInfoContent = ref('')
const editTextareaRefs = ref<Record<number,HTMLTextAreaElement>>({})

//连线备注相关
// 连线备注浮动编辑框
const editingEdgeForLabel = ref<any>(null)        // 当前编辑的边对象
const editEdgeLabelText = ref('')                 // 临时备注文本
const editEdgePosition = ref({ x: 0, y: 0 })      // 输入框坐标
const edgeEditInput = ref<HTMLInputElement | null>(null)
// 默认边的样式配置（包括标签字体大小）
const defaultEdgeOptions = {
  labelStyle: {
    fontSize: '18px',
    fontWeight: 'bold',
    fill: '#333',
  },
  labelBgStyle: {
    fill: 'transparent',   /* ← 背景透明 */
  },
  labelBgPadding: [4, 4] as [number,number],
  labelBgBorderRadius: 4,
  style: {
    stroke: '#b1b1b7',
    strokeWidth: 2,
  },
}


// 自动滚动到底部
watch(chatHistory, () => {
  nextTick(() => {
    if (chatMessages.value) {
      chatMessages.value.scrollTop = chatMessages.value.scrollHeight
    }
  })
}, { deep: true })

// 当展开有板块时自动滚动到底部
watch([activeTab, panelOpen], async ([tab, open]) => {
  if (tab === 'chat' && open) {
    await nextTick()
    scrollToBottom()
  }
})



onMounted(async () => {
  await loadNotes()
  await loadConnections()
  await loadTimelineEvents()
  await loadChatHistory()
  await loadDocuments()
  await loadKnownInfos()
  await nextTick()
  goToCenter()
})



//markdown 相关
function renderMarkdown(text: string) {
  if (!text) return ''
  const rawHtml = marked(text) as string
  return DOMPurify.sanitize(rawHtml)
}

// 加载对话历史
async function loadChatHistory() {
  try {
    const res = await getAgentHistory(caseId)
    chatHistory.value = res.data.map((m: any) => ({
      role: m.role,
      content: m.content,
    }))
  } catch (err) {
    console.error('加载对话历史失败', err)
  }
}

//发送信息
async function sendMessage() {
  const msg = chatInput.value.trim()
  if (!msg || chatLoading.value) return

  chatInput.value = ''
  chatHistory.value.push({ role: 'user', content: msg })
  chatLoading.value = true
  isThinking.value = true

  const assistantMsg = reactive({ role: 'assistant', content: '' })
  chatHistory.value.push(assistantMsg)
  
  await nextTick()
  scrollToBottom()

  try {
    const response = await fetch(`http://127.0.0.1:8001/cases/${caseId}/agent/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg }),
    })

    if (!response.ok) throw new Error('Request failed')
    const reader = response.body?.getReader()
    if (!reader) throw new Error('No reader')

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') continue

          if (isThinking.value) {
            isThinking.value = false
          }
          assistantMsg.content += data
          await nextTick()
          scrollToBottom()
        }
      }
    }
  } catch (err) {
    console.error('流式对话失败', err)
    isThinking.value = false
    if (!assistantMsg.content) assistantMsg.content = '抱歉，请求失败，请稍后重试。'
  } finally {
    chatLoading.value = false
    isThinking.value = false
    await loadChatHistory()
    nextTick(() => {
      chatInputRef.value?.focus()
    })
  }
}

//判断回车是否是发送信息
function handleEnterKey(event:KeyboardEvent) {
  if (event.isComposing){
    return
  }
  sendMessage()
}

//回到聊天底部
function scrollToBottom() {
  if (chatMessages.value) {
    chatMessages.value.scrollTop = chatMessages.value.scrollHeight
  }
}


// 软清空：只清界面，不调后端
function clearScreen() {
  chatHistory.value = []
}


// 清空对话
async function resetMemory() {
  if (!confirm('确定要重置吗?这将消除助手小姐关于本案的所有记忆,重新开始.')) return
  try {
    await clearAgentHistory(caseId)
    chatHistory.value = []
  } catch (err) {
    console.error('重置记忆失败', err)
  }
}


// 修正日期
function fixDate() {
  // 月份限制在 1-12
  if (eventMonth.value < 1) eventMonth.value = 1
  if (eventMonth.value > 12) eventMonth.value = 12
  
  // 根据月份和年份计算最大天数
  const daysInMonth = new Date(eventYear.value, eventMonth.value, 0).getDate()
  if (eventDay.value < 1) eventDay.value = 1
  if (eventDay.value > daysInMonth) eventDay.value = daysInMonth
}

// 修正时间
function fixTime() {
  if (eventHour.value < 0) eventHour.value = 0
  if (eventHour.value > 23) eventHour.value = 23
  if (eventMinute.value < 0) eventMinute.value = 0
  if (eventMinute.value > 59) eventMinute.value = 59
}


// 排序
const sortedEvents = computed(() => {
  return [...timelineEvents.value].sort((a, b) => {
    return parseEventTime(a.event_time) - parseEventTime(b.event_time)
  })
})

//规范时间
function formatEventTime(eventTime: string) {
  if (!eventTime) return ''
  const match = eventTime.match(/(\d+)年(\d+)月(\d+)日/)
  if (match) {
    return `${match[2]}/${match[3]}`
  }
  return eventTime
}

//获取时间点在时间轴上的位置
function getDotPosition(event: any, events: any[]) {
  if (events.length <= 1) return 50

  const sorted = [...events].sort((a, b) => parseEventTime(a.event_time) - parseEventTime(b.event_time))
  const firstTime = parseEventTime(sorted[0].event_time)
  const lastTime = parseEventTime(sorted[sorted.length - 1].event_time)
  const totalRange = lastTime - firstTime || 1

  // 计算所有事件的理想百分比
  const items = sorted.map(e => ({
    id: e.id,
    ideal: ((parseEventTime(e.event_time) - firstTime) / totalRange) * 100,
  }))

  // 只从左到右推，保证最小间距
  const minSpacing = 5
  for (let i = 1; i < items.length; i++) {
    const gap = items[i].ideal - items[i - 1].ideal
    if (gap < minSpacing) {
      items[i].ideal = items[i - 1].ideal + minSpacing
    }
  }

  // 如果最右边的点超出了 98%，整体压缩
  const maxIdeal = items[items.length - 1].ideal
  const scale = maxIdeal > 98 ? 98 / maxIdeal : 1

  const item = items.find(a => a.id === event.id)
  if (!item) return 50

  return Math.max(2, item.ideal * scale)
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


//加载

async function loadNotes() {
  try {
    const res = await getNotes(caseId)
    const serverNotes = res.data
    nodes.value = serverNotes.map((n: any) => ({
      id: String(n.id),
      type: 'note',
      position: { x: n.pos_x, y: n.pos_y },
      data: {
        content: n.content,
        type: n.type,
        color: n.color,
        name: n.name || '',          // ← 这一行必须有
      },
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
  const defaultColors: Record<string, string> = {
    clue: '#FFF9C4',
    suspect: '#FFCCBC',
  }
  const defaultName = type === 'suspect' ? '未知' : ''
  try {
    const res = await createNote(caseId, {
      type,
      content: type === 'clue' ? '新线索' : '新嫌疑人',
      name: defaultName,
      color: defaultColors[type],
      pos_x: Math.random() * 400,
      pos_y: Math.random() * 300,
      width: 200,
      height: 120,
    })
    nodes.value.push({
      id: String(res.data.id),
      type: 'note',
      position: { x: res.data.pos_x, y: res.data.pos_y },
      data: {
        content: res.data.content,
        type: res.data.type,
        name: res.data.name || '',
        color: res.data.color,
      },
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

  if (source === target) return

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
  panelOpen.value = true
  activeTab.value = 'edit'
}

function deselectNode() {
  selectedNode.value = null
}

async function saveSelectedNode() {
  if (!selectedNode.value) return
  const n = selectedNode.value
  try {
    await updateNote(caseId, Number(n.id), {
      content: n.data.content,
      type: n.data.type,
      color: n.data.color,
      name: n.data.name || '',
    })
    // 同步更新本地节点数据，保存后立即显示名字
    const idx = nodes.value.findIndex(node => node.id === n.id)
    if (idx !== -1) {
      nodes.value[idx].data = { ...n.data }
    }
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

//删除时间点事件
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

//文档相关
async function loadDocuments(){
  try{
    const res = await getDocument(caseId)
    docList.value = res.data
  }catch(err) {
    console.error('加载文档列表失败',err)
  }
}

//<input type="file" ref="fileInput" style="display: none;" @change="handleUpload" />
//模板中有上面那句 意思是将原有的文件上传按钮隐藏,因为他们往往位置不固定
//这个函数就是当用户点击我们设计好的区域时,自动模拟点击了原生上传按钮
function triggerFileInput(){
  fileInput.value?.click()
}

//当用户将文件加载进上传框时,拿到这个上传框元素,进而拿到文件将其上传
async function handleFileSelect(event:Event){
  const input = event.target as HTMLInputElement
  if (input.files &&input.files.length){
    await uploadDocFile(input.files[0])
    input.value = ""
  }

}

//拖拽添加文件时,拿到拖拽文件 将其上传
async function handleDrop(event:DragEvent){
  const files = event.dataTransfer?.files
  if(files && files.length){
    await uploadDocFile(files[0])
  }
}

async function uploadDocFile(file:File){
  if(!file.name.endsWith('.txt')){
    alert('抱歉,目前只支持txt文件')
    return 
  }
  uploading.value = true
  try{
    await uploadDocument(caseId,file)
    await loadDocuments()
    alert('上传成功')
  }catch(err:any){
    console.error('上传失败',err)
    alert(err.response?.data?.detail || '上传失败')
  }finally{
    uploading.value = false
  }
}

//已知信息相关
async function loadKnownInfos(){
  try{
    const res = await getKnownInfos(caseId)
    knownInfos.value = res.data

  }catch(err){
    console.error('加载已知信息失败',err)
  }

}

async function addKnownInfo(){
  const content = newInfoContent.value.trim()
  if (!content) return
  try {
    await createKnownInfo(caseId,content)
    newInfoContent.value = ''
    await loadKnownInfos()
  }catch(err){
    console.error('添加失败',err)
  }
}

function startEditInfo(info:any){
  editingId.value = info.id
  editInfoContent.value = info.content
  nextTick(() => {
    setTimeout(() => {
      const ta = editTextareaRefs.value[info.id]
      if (ta) {
        ta.focus()
        // 可选：把光标放到末尾
        ta.selectionStart = ta.selectionEnd = ta.value.length
      }
    }, 0)
  })
}

async function saveEditInfo(info:any){
  if(!editingId.value) return
  const newContent = editInfoContent.value.trim()
  if (newContent && newContent !== info.content){
    try{
      await updateKnownInfo(caseId,info.id,newContent)
      await loadKnownInfos()
    }catch(err){
      console.error('更新失败',err)
    }
  }
  editingId.value = null
  editInfoContent.value = ''
}

async function deleteKnownInfoItem(infoId:number){
  if(!confirm('确定删除该条信息吗')) return
  try {
    await deleteKnownInfo(caseId,infoId)
    await loadKnownInfos()
  }catch(err){
    console.error('删除失败',err)
  }
}


// 连线相关


function onEdgeDoubleClick(params: any) {
  const { edge, event } = params
  event.stopPropagation()
  
  // 直接用鼠标坐标
  editingEdgeForLabel.value = edge
  editEdgeLabelText.value = edge.label || ''
  editEdgePosition.value = { x: event.clientX, y: event.clientY }
  
  nextTick(() => {
    edgeEditInput.value?.focus()
  })
}

async function saveEdgeLabelEdit() {
  if (!editingEdgeForLabel.value) return
  const edge = editingEdgeForLabel.value
  const newLabel = editEdgeLabelText.value.trim()
  const oldLabel = edge.label || ''
  
  if (newLabel !== oldLabel) {
    try {
      await updateConnection(caseId, parseInt(edge.id), { label: newLabel })
      // 更新本地 edges 数据
      const targetEdge = edges.value.find(e => e.id === edge.id)
      if (targetEdge) targetEdge.label = newLabel
    } catch (err) {
      console.error('保存连线备注失败', err)
      alert('保存失败，请重试')
    }
  }
  // 关闭浮窗
  editingEdgeForLabel.value = null
  editEdgeLabelText.value = ''
}

async function deleteCurrentEdge() {
  if (!editingEdgeForLabel.value) {
    return
  }
  const edge = editingEdgeForLabel.value
  const edgeId = edge.id

  if (!confirm('确定要删除这条连线吗？')) {
    return
  }

  // 先关闭浮窗，避免二次操作
  const edgeToDelete = edge
  editingEdgeForLabel.value = null
  editEdgeLabelText.value = ''

  try {
    await deleteConnection(caseId, parseInt(edgeId))
    edges.value = edges.value.filter(e => e.id !== edgeId)
  } catch (err: any) {
    console.error('删除连线失败', err)
    alert('删除失败：' + (err.response?.data?.detail || err.message))

    editingEdgeForLabel.value = edgeToDelete
    editEdgeLabelText.value = edgeToDelete.label || ''
  }
}
</script>

<style scoped>
:root {
  --gold: #D4A843;
  --gold-light: #FFF5D6;
  --gold-pale: #FFF8E8;
  --gold-deep: #B8922E;
  --traveler-blue: #3A7BC8;
  --white: #FFFFFF;
  --cream: #FFFBF0;
  --text: #2D2D2D;
  --text-secondary: #6B6B6B;
  --border: #E8D9B0;
  --shadow: 0 2px 12px rgba(184, 146, 46, 0.08);
  --shadow-hover: 0 8px 24px rgba(184, 146, 46, 0.16);
}


.case-detail {
  height: 100vh;
  display: flex;
  flex-direction: column;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", Helvetica, Arial, sans-serif;
}

/* 时间线顶栏 */
.timeline-bar {
  height: 48px;
  background: linear-gradient(135deg, var(--gold), var(--gold-deep));
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 2px 8px rgba(184, 146, 46, 0.25);
  position: relative;
  z-index: 10;
  flex-shrink: 0;
}

.timeline-bar::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--gold), transparent);
}

/* 添加事件的按钮 */
.timeline-bar button {
  padding: 6px 14px;
  background: #fff;
  border: 1.5px solid #D4A843;
  border-radius: 16px;
  color: #B8922E;
  font-weight: 600;
  font-size: 13px;
  cursor: pointer;
  outline: none;
  transition: all 0.2s;
}
.timeline-bar button:hover {
  background: #D4A843;
  color: #fff;
  border-color: #B8922E;
}

/* 返回按钮 */
.back-btn {
  color: var(--white);
  text-decoration: none;
  font-size: 20px;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(255,255,255,0.2);
  transition: all 0.3s;
}

.back-btn:hover {
  background: rgba(255,255,255,0.35);
  transform: scale(1.1);
}

/* 时间线面板 */
.timeline-panel {
  background: #F8F5EC;
  border-bottom: 1px solid #E0D5C0;
  padding: 12px 24px;
  position: relative;
  box-sizing: border-box;
}

.timeline-form {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 4px;
}
.datetime-picker {
  display: flex;
  gap: 2px;
  align-items: center;
  background: var(--white);
  padding: 4px 8px;
  border-radius: 8px;
  border: 1px solid #D4C9A8;
}

.datetime-picker input {
  width: 42px;
  padding: 3px 4px;
  border: none;
  border-radius: 4px;
  text-align: center;
  font-size: 12px;
  background: transparent;
  color: var(--text);
}
.datetime-picker input:first-child {
  width: 52px;   /* 年份加宽 */
}

.datetime-picker input:focus {
  outline: none;
  background: var(--gold-pale);
}

.datetime-picker span {
  color: #B8A88A;
  font-weight: bold;
  font-size: 12px;
}

.timeline-form input[type="text"] {
  flex: 1;
  min-width: 160px;
  padding: 8px 14px;
  border: 1.5px solid #C4B99A;
  border-radius: 20px;
  font-size: 13px;
  background: #fff;
  outline: none;
  font-family: inherit;
  transition: border-color 0.2s;
}

.timeline-form input[type="text"]:focus {
  border-color: #D4A843;
}

.timeline-form button {
  padding: 8px 18px;
  background: #D4A843;
  border: 1.5px solid #B8922E;
  border-radius: 20px;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
  font-size: 12px;
  outline: none;
  transition: all 0.2s;
}


.timeline-form button:hover {
  background: #B8922E;
  border-color: #9A7A28;
  transform: translateY(-1px);
}

.timeline-axis {
  position: relative;
  height: 40px;           /* ← 从 56px 减小 */
  margin: 8px 40px 0;     /* ← 上边距给表单留空间 */
  display: flex;
  align-items: center;     /* 垂直居中 */
}

.axis-line {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 2px;            /* ← 从 3px 变细 */
  transform: translateY(-50%);
  background: linear-gradient(90deg, transparent, #D4C9A8, #C4B99A, #D4C9A8, transparent);
  border-radius: 1px;
}

.timeline-dot-wrapper {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);  /* ← 同时水平和垂直居中 */
  text-align: center;
  z-index: 2;
}

.timeline-dot {
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: transform 0.3s;
}

.timeline-dot:hover {
  transform: scale(1.15);
}


.dot {
  width: 14px;            /* ← 从 16px 稍小 */
  height: 14px;
  background: var(--white);
  border-radius: 50%;
  border: 2.5px solid #9A7A28;  /* ← 边框稍细 */
  box-shadow: 0 0 0 3px rgba(212, 168, 67, 0.2);
  transition: all 0.3s;
}

.timeline-dot:hover .dot {
  border-color: #D4A843;
  box-shadow: 0 0 0 5px rgba(212, 168, 67, 0.25);
  transform: scale(1.1);
}


.dot-time {
  position: absolute;
  top: 22px;      
  left: 50%;
  transform: translateX(-50%);
  font-size: 10px;
  color: #8B7D6B;
  font-weight: 600;
  white-space: nowrap;
  background: var(--white);
  padding: 2px 6px;
  border-radius: 6px;
  border: 1px solid #E0D5C0;
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

/* 回到中心按钮 */
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

/* 右侧面板 */
.side-panel {
  width: 380px;
  border-left: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(16px);
  overflow-y: auto;
  position: relative;
  transition: width 0.3s ease;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  overflow-x: hidden;
  box-sizing: border-box;
}

.side-panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--gold), var(--gold-deep), var(--traveler-blue));
}

.side-panel.collapsed {
  width: 40px;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
  background: rgba(255, 248, 220, 0.5);
  flex-shrink: 0;
}

.toggle-panel-btn {
  background: var(--white);
  border: 2px solid var(--gold);
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 14px;
  color: var(--gold-deep);
  transition: all 0.3s;
  padding: 0;
  flex-shrink: 0;
}

.toggle-panel-btn:hover {
  background: var(--gold);
  color: var(--white);
  transform: rotate(180deg);
}


.panel-header h3 {
  margin: 0;
  white-space: nowrap;
}
.panel-content {
  padding: 16px;
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  box-sizing: border-box;
  width: 100%;
}

/* 编辑区 */
textarea {
  resize: none;
  width: 100%;
  min-height: 80px;
  padding: 10px 14px;
  border: 2px solid #ffe79e;   /* ← 加深，常驻可见 */
  border-radius: 12px;
  font-size: 14px;
  background: var(--white);
  transition: all 0.3s;
  outline: none;                /* ← 去掉浏览器默认黑框 */
  box-sizing: border-box;       /* ← padding和border不增加宽度 */
  font-family: inherit;
}


textarea:focus {
  /* border-color: var(--gold); */
  box-shadow: 0 0 0 4px rgba(255, 215, 0, 0.35);  /* ← 更耀眼的金色光晕 */
}

.color-picker {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 12px 0;
}

.color-swatch {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 3px solid transparent;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 2px 6px rgba(0,0,0,0.1);
}

.color-swatch:hover {
  transform: scale(1.2);
}

.color-swatch.active {
  border-color: var(--gold-deep);
  box-shadow: 0 0 0 3px rgba(212, 168, 67, 0.2);
}
.suspect-name-input {
  width: 100%;
  padding: 10px 14px;
  border: 2px solid #ffe79e;
  border-radius: 12px;
  font-size: 14px;
  background: var(--white);
  outline: none;
  box-sizing: border-box;
  font-family: inherit;
  transition: all 0.3s;
}

.suspect-name-input:focus {
  box-shadow: 0 0 0 4px rgba(255, 215, 0, 0.35);
}

.suspect-name-input:focus {
  box-shadow: 0 0 0 4px rgba(255, 215, 0, 0.35);
}

.edit-btn {
  padding: 8px 18px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  outline: none;
  transition: all 0.2s;
  border: 1.5px solid;
}

.save-btn {
  background: #D4A843;
  border-color: #B8922E;
  color: #fff;
  margin-right:10px;
}

.save-btn:hover {
  background: #B8922E;
  border-color: #9A7A28;
  transform: translateY(-1px);
}

.delete-btn {
  background: #fff;
  border-color: #e75765;
  color: #c62828;
}

.delete-btn:hover {
  background: #ffebee;
  border-color: #c62828;
  transform: translateY(-1px);
}
/* 对话 Tab */
.tab-buttons {
  display: flex;
  gap: 6px;
}

.tab-buttons button {
  padding: 6px 16px;
  background: transparent;
  border: 2px solid transparent;
  border-radius: 20px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  transition: all 0.3s;
}

.tab-buttons button:hover {
  background: rgba(212, 168, 67, 0.08);
  color: var(--gold-deep);
}

.tab-buttons button.active {
  background: linear-gradient(135deg, var(--gold), var(--gold-deep));
  color: var(--white);
  border-color: transparent;
  box-shadow: 0 2px 8px rgba(212, 168, 67, 0.25);
}


.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 0;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: 
    radial-gradient(circle at 0% 100%, rgba(212, 168, 67, 0.04) 0%, transparent 40%),
    radial-gradient(circle at 100% 0%, rgba(58, 123, 200, 0.04) 0%, transparent 40%),
    var(--cream);
}

.chat-empty {
  color: var(--gold-deep);
  text-align: center;
  margin-top: 80px;
  font-size: 15px;
  opacity: 0.7;
}

.chat-msg {
  display: flex;
  flex-direction: column;
  margin-bottom: 16px;
  animation: fadeInUp 0.4s ease;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.chat-msg.user {
  align-items: flex-end;
}
.chat-msg.assistant {
  align-items: flex-start;
}

/* 头像 */
.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  margin-bottom: 6px;
  border: 3px solid var(--white);
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  background: #e0e0e0;
  display: block;
}

.avatar[src=""], .avatar:not([src]) {
  background: #e0e0e0;
}

.chat-msg.user .avatar {
  background: linear-gradient(135deg, var(--traveler-blue), #5B9BD5);
}

.chat-msg.assistant .avatar {
  background: linear-gradient(135deg, var(--gold), var(--gold-deep));
}

/* 气泡 */
.msg-bubble {
  max-width: 85%;
  min-width: 60px;
  padding: 12px 16px;
  border-radius: 18px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  position: relative;
}

.chat-msg.user .msg-bubble {
  background: linear-gradient(135deg, var(--traveler-blue), #4A8FD0);
  color: var(--white);
  border: none;
  border-bottom-right-radius: 4px;
  box-shadow: 0 4px 16px rgba(58, 123, 200, 0.2);
}

.chat-msg.assistant .msg-bubble {
  background: var(--white);
  border: 1px solid var(--border);
  border-bottom-left-radius: 4px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.06);
}

/* Markdown 内容样式 */
.msg-bubble :deep(p) {
  margin: 0 0 6px;
}

.msg-bubble :deep(p):last-child {
  margin-bottom: 0;
}

.msg-bubble :deep(strong) {
  color: var(--gold-deep);
  font-weight: 700;
}

.msg-bubble :deep(ul), .msg-bubble :deep(ol) {
  padding-left: 20px;
  margin: 4px 0;
}
.msg-bubble :deep(code) {
  background: var(--gold-pale);
  color: var(--gold-deep);
  padding: 2px 6px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.msg-bubble :deep(pre) {
  background: #2D2D2D;
  color: #F0E6C8;
  padding: 12px;
  border-radius: 12px;
  overflow-x: auto;
  font-size: 12px;
  margin: 8px 0;
}

/* 输入区 */
.chat-input {
  border-top: 2px solid var(--border);
  padding: 12px 16px;
  display: flex;
  gap: 8px;
  background: var(--white);
  position: relative;
  padding-right: 22px;
}

.chat-input::before {
  content: '';
  position: absolute;
  top: -2px;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, var(--gold), var(--traveler-blue));
}

.chat-input input {
  flex: 1;
  padding: 10px 18px;
  border: 2px solid #efd587;
  border-radius: 24px;
  font-size: 14px;
  background: var(--cream);
  transition: all 0.3s;
  font-family: inherit;
}

.chat-input input:focus {
  outline: none;
  background: var(--white);
  box-shadow: 0 0 0 4px rgba(212, 168, 67, 0.35);
}

.chat-input input::placeholder {
  color: var(--text-secondary);
  opacity: 0.6;
}

.chat-input button {
  padding: 8px 14px;
  border-radius: 20px;
  border: none;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.3s;
  outline:none;
}

.chat-input button:first-of-type {
  background: linear-gradient(135deg, var(--gold), var(--gold-deep));
  color: var(--white);
  box-shadow: 0 2px 8px rgba(212, 168, 67, 0.25);
  border: 2px solid #efd587
}

.chat-input button:first-of-type:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(212, 168, 67, 0.35);
}

.chat-input button:first-of-type:disabled {
  opacity: 0.5;
  transform: none;
  cursor: not-allowed;
}

.chat-input button:not(:first-of-type) {
  background: var(--white);
  color: var(--text-secondary);
  border: 2px solid #efd587;
  outline:none;
}

.chat-input button:not(:first-of-type):hover {
  /* border-color: var(--gold); */
  color: var(--gold-deep);
  transform: translateY(-2px); 
  outline:none;
}

/* 重置按钮 */
.chat-input button.reset-btn {
  background: var(--white);
  color: #c62828;
  border: 2px solid #e75765;
}

.chat-input button.reset-btn:hover {
  background: #ffebee;
  border-color: #c62828;
  color: #c62828 !important;
  transform: translateY(-2px);
}
/* 上传文档相关 */
.upload-area {
  border: 3px dashed var(--gold);
  border-radius: 16px;
  padding: 32px 24px;
  text-align: center;
  cursor: pointer;
  margin-bottom: 20px;
  background: linear-gradient(135deg, rgba(255, 248, 220, 0.5), rgba(255, 250, 205, 0.3));
  transition: all 0.3s;
  position: relative;
  overflow: hidden;
}

.upload-area::before {
  content: '✦';
  position: absolute;
  top: 8px;
  right: 12px;
  font-size: 24px;
  color: var(--gold);
  opacity: 0.3;
}

.upload-area:hover {
  background: linear-gradient(135deg, rgba(255, 248, 220, 0.8), rgba(255, 250, 205, 0.5));
  border-color: var(--gold-deep);
  transform: translateY(-2px);
  box-shadow: var(--shadow-hover);
}

.upload-area p:first-child {
  font-size: 16px;
  font-weight: 600;
  color: var(--gold-deep);
  margin-bottom: 8px;
}

.upload-area p:last-child {
  font-size: 12px;
  color: var(--text-secondary);
}


.doc-list {
  background: var(--white);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid var(--border);
}

.doc-list h4 {
  font-size: 14px;
  font-weight: 700;
  color: var(--gold-deep);
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.doc-list h4::before {
  content: '📄';
}

.doc-list li {
  padding: 8px 12px;
  background: var(--gold-pale);
  border-radius: 8px;
  margin-bottom: 6px;
  font-size: 13px;
  color: var(--text);
  border-left: 3px solid var(--gold);
}


.upload-progress {
  color: var(--gold-deep);
  font-size: 12px;
  margin-bottom: 8px;
  text-align: center;
  font-weight: 500;
}


/* 已知信息板块 */
.known-info-form {
  margin-bottom: 12px;
  width: 100%;
  box-sizing: border-box;
}

.known-info-form textarea {
  width: 100%;
  padding: 12px;
  border: 2px solid #ffe79e;
  border-radius: 12px;
  font-size: 14px;
  resize: none;
  box-sizing: border-box;
  margin: 0;                    /* ← 去掉margin-left:10px */
  background: var(--white);
  transition: all 0.3s;
  outline: none;
  font-family: inherit;
}

.known-info-form textarea:focus {
  /* border-color: var(--gold); */
  box-shadow: 0 0 0 4px rgba(255, 215, 0, 0.35);
}

.known-info-button {
  padding: 8px 24px;
  background: linear-gradient(135deg, var(--gold), var(--gold-deep));
  color: var(--white);
  border: none;
  border-radius: 12px;
  cursor: pointer;
  margin: 10px 0 0 0;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(212, 168, 67, 0.25);
  transition: all 0.3s;
}

.known-info-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(212, 168, 67, 0.35);
}


.info-hint {
  font-size: 12px;
  color: var(--gold-deep);
  margin: 12px 0;
  padding: 8px 12px;
  background: var(--gold-pale);
  border-radius: 8px;
  border-left: 3px solid var(--gold);
}

.known-info-list {
  list-style: none;
  padding: 0;
  margin: 0;
  width: 100%;
  box-sizing: border-box;
}

.known-info-list li {
  background: var(--white);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px;
  margin-bottom: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.3s;
  width: 100%;
  box-sizing: border-box;
}

.known-info-list li:hover {
  border-color: var(--gold);
  box-shadow: var(--shadow);
  transform: translateX(4px);
}


.info-content {
  flex: 1;
  cursor: pointer;
  word-break: break-word;
  min-width: 0;
  border: 1px solid #D4C9A8;   /* ← 加这个 */
  border-radius: 6px;
  padding: 6px 8px;
  background: var(--white);
  transition: all 0.3s;
}

.info-content.editing {
  border-color: transparent;
  background: transparent;
  padding:0;
}

.info-content textarea {
  width: 100%;
  padding: 4px;
  font-size: 12px;
  border: 1px solid #ffe79e;   /* ← 加深，常驻可见 */
  border-radius: 4px;
  resize: none;
  box-sizing: border-box;       /* ← 确保不溢出 */
  outline: none;
  font-family: inherit;
}

.info-content textarea:focus {
  /* border-color: var(--gold); */
  box-shadow: 0 0 0 3px rgba(255, 215, 0, 0.35);
}

.info-actions button {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  padding: 0 4px;
  opacity: 0.6;
}

.info-actions button:hover {
  opacity: 1;
}

.empty-info {
  color: var(--text-secondary);
  text-align: center;
  padding: 40px 20px;
  font-size: 14px;
}

.empty-info::before {
  content: '✦';
  display: block;
  font-size: 36px;
  color: var(--gold);
  margin-bottom: 12px;
  opacity: 0.5;
}

/* 连线备注相关 */
/* 连线备注工具栏：包含输入框和删除按钮，整体居中 */
.edge-edit-toolbar {
  position: fixed;
  transform: translate(-50%, -50%);
  z-index: 1000;
  display: flex;
  gap: 10px;
  align-items: center;
  background: transparent;
}

/* 输入框容器（带圆角白背景和阴影） */
.edge-edit-input-wrapper {
  background: rgba(255, 255, 255, 0.6);   /* 半透明白 */
  backdrop-filter: blur(4px);               /* 毛玻璃效果 */
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

/* 独立的删除按钮（圆形） */
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


/* 提示信息 */
/* 思考提示容器 */
.thinking-text {
  color: var(--gold-deep);
  font-style: italic;
  font-size: 14px;
  animation: blink 1.5s ease-in-out infinite;
  display: flex;
  align-items: center;
  gap: 8px;
}

.thinking-text::before {
  content: '✦';
  font-size: 16px;
  animation: spin 2s linear infinite;
}

.thinking-dots {
  display: inline-block;
  animation: blink 1.5s ease-in-out infinite;
  animation-delay: 0.3s;
}

@keyframes blink {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 滚动条美化 */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: var(--gold);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--gold-deep);
}

.timeline-toggle {
  color: var(--white);
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  text-shadow: 0 1px 2px rgba(0,0,0,0.1);
}

.timeline-toggle span {
  font-size: 12px;
  opacity: 0.8;
}
</style>