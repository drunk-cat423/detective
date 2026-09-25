<template>
  <div class="case-detail">
    <!-- 顶部时间线 -->
    <TimelineBar
      v-model:open="timelineOpen"
      v-model:search-query="searchQuery"
      :show-add="showAddEvent"
      @toggle-add="showAddEvent = !showAddEvent"
    />

    <!-- 时间线内容区：保持挂载，让展开/收起可以平滑反向。 -->
    <div id="case-timeline" class="timeline-reveal" :class="{ open: timelineOpen }" :aria-hidden="!timelineOpen">
      <div class="timeline-reveal-inner">
        <TimelinePanel
          v-model:eventYear="eventYear"
          v-model:eventMonth="eventMonth"
          v-model:eventDay="eventDay"
          v-model:eventHour="eventHour"
          v-model:eventMinute="eventMinute"
          v-model:newEventDesc="newEventDesc"
          :show-form="showAddEvent"
          :sorted-events="sortedEvents"
          :hovered-event="hoveredEvent"
          :locked-events="lockedEvents"
          @submit="addTimelineEvent"
          @delete="handleDeleteEvent"
          @show-popup="showPopup"
          @dot-mouse-leave="onDotMouseLeave"
          @popup-mouse-enter="onPopupMouseEnter"
          @popup-mouse-leave="onPopupMouseLeave"
          @lock-popup="lockPopup"
          @close-popup="closePopup"
          @close-all="closeAllPopups"
        />
      </div>
    </div>

    <!-- 主区域 -->
    <div class="main-area">
      <!-- 便签墙画布 -->
      <NoteCanvas
        v-model:nodes="nodes"
        v-model:edges="edges"
        :editing-edge-for-label="editingEdgeForLabel"
        v-model:edit-edge-label-text="editEdgeLabelText"
        :edit-edge-position="editEdgePosition"
        :default-edge-options="defaultEdgeOptions"
        :search-query="searchQuery"
        :panel-open="panelOpen"
        @select-node="handleSelectNode"
        @open-node-editor="handleOpenNodeEditor"
        @deselect-node="deselectNode"
        @go-to-center="handleGoToCenter"
        @on-connect="onConnect"
        @on-nodes-change="onNodesChange"
        @on-edge-double-click="onEdgeDoubleClick"
        @save-edge-label-edit="saveEdgeLabelEdit"
        @delete-current-edge="deleteCurrentEdge"
        @add-note="handleAddNote"
        @delete-node="handleDeleteNode"
      />

      <!-- 右侧面板 -->
      <SidePanel
        v-model:open="panelOpen"
        v-model:activeTab="activeTab"
      >
        <!-- 对话 Tab -->
        <ChatTab
          v-if="activeTab === 'chat'"
          v-model:chatInput="chatInput"
          :chat-history="chatHistory"
          :chat-loading="chatLoading"
          :is-thinking="isThinking"
          :user-avatar="userAvatar"
          :agent-avatar="agentAvatar"
          @send="sendMessage"
          @clear="clearScreen"
          @reset="resetMemory"
          @enter-key="handleEnterKey"
          @mounted="scrollChatToBottom"
        />

        <!-- 文档 Tab -->
        <DocsTab
          v-else-if="activeTab === 'docs'"
          v-model:fileInputRef="fileInput"
          :uploading="uploading"
          :doc-list="docList"
          @trigger="triggerFileInput"
          @file-select="handleFileSelect"
          @drop="handleDrop"
          @remove="removeDocument"
        />

        <!-- 已知信息 Tab -->
        <InfoTab
          v-else
          v-model:newInfoContent="newInfoContent"
          :known-infos="knownInfos"
          :editing-id="editingId"
          :edit-info-content="editInfoContent"
          :edit-textarea-refs="editTextareaRefs"
          @add="addKnownInfo"
          @start-edit="startEditInfo"
          @save-edit="saveEditInfo"
          @delete="deleteKnownInfoItem"
        />
      </SidePanel>
    </div>

    <Transition name="card-editor-overlay">
      <div
        v-if="editorNode"
        class="card-editor-overlay"
        :style="editorOverlayStyle"
        @click.self="closeCardEditor"
      >
        <CardEditorOverlay
          :node="editorNode"
          :preset-colors="presetColors"
          @save="handleEditorSave"
          @delete="handleEditorDelete"
          @close="closeCardEditor"
        />
      </div>
    </Transition>

    <Transition name="toast">
      <div v-if="toastMessage" class="case-toast" role="status">{{ toastMessage }}</div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, nextTick, watch } from 'vue'

import TimelineBar from '@/components/timeline/TimelineBar.vue'
import TimelinePanel from '@/components/timeline/TimelinePanel.vue'
import NoteCanvas from '@/components/canvas/NoteCanvas.vue'
import CardEditorOverlay from '@/components/canvas/CardEditorOverlay.vue'
import SidePanel from '@/components/sidebar/SidePanel.vue'
import ChatTab from '@/components/sidebar/ChatTab.vue'
import DocsTab from '@/components/sidebar/DocsTab.vue'
import InfoTab from '@/components/sidebar/InfoTab.vue'

import { useNotes } from '@/composables/useNotes'
import { useTimeline } from '@/composables/useTimeline'
import { useChat } from '@/composables/useChat'
import { useKnownInfo } from '@/composables/useKnownInfo'
import { useDocuments } from '@/composables/useDocuments'

const props = defineProps<{ id: string }>()
const caseId = Number(props.id)

// 侧边栏状态
const panelOpen = ref(false)
const searchQuery = ref('')
const activeTab = ref<'chat' | 'docs' | 'info'>('chat')
const toastMessage = ref('')
let toastTimer: ReturnType<typeof setTimeout> | undefined
const editorNode = ref<any | null>(null)
const editorMotion = ref({ x: 0, y: 0, scaleX: .36, scaleY: .25 })
const editorOverlayStyle = computed(() => ({
  '--editor-origin-x': `${editorMotion.value.x}px`,
  '--editor-origin-y': `${editorMotion.value.y}px`,
  '--editor-origin-scale-x': editorMotion.value.scaleX,
  '--editor-origin-scale-y': editorMotion.value.scaleY,
}))

// Notes composable
const {
  nodes, edges, selectedNode, presetColors,
  editingEdgeForLabel, editEdgeLabelText, editEdgePosition, defaultEdgeOptions,
  loadNotes, loadConnections, addNote, onConnect, onNodesChange,
  selectNode, deselectNode, saveSelectedNode, deleteSelectedNode,
  goToCenter, onEdgeDoubleClick, saveEdgeLabelEdit, deleteCurrentEdge,
} = useNotes(caseId)

// Timeline composable
const {
  timelineOpen, showAddEvent,
  eventYear, eventMonth, eventDay, eventHour, eventMinute, newEventDesc,
  hoveredEvent, lockedEvents, sortedEvents,
  addTimelineEvent, handleDeleteEvent, loadTimelineEvents,
  showPopup, onDotMouseLeave, onPopupMouseEnter, onPopupMouseLeave,
  lockPopup, closePopup, closeAllPopups,
} = useTimeline(caseId)

// Chat composable
const {
  chatHistory, chatInput, chatLoading, isThinking, userAvatar, agentAvatar,
  sendMessage, clearScreen, resetMemory, loadChatHistory, handleEnterKey,
} = useChat(caseId)

// KnownInfo composable
const {
  knownInfos, newInfoContent, editingId, editInfoContent, editTextareaRefs,
  loadKnownInfos, addKnownInfo, startEditInfo, saveEditInfo, deleteKnownInfoItem,
} = useKnownInfo(caseId)

// Documents composable
const {
  fileInput, uploading, docList,
  loadDocuments, triggerFileInput, handleFileSelect, handleDrop, removeDocument,
} = useDocuments(caseId)

// 当展开聊天面板时自动滚动到底部
watch([activeTab, panelOpen], async ([tab, open]) => {
  if (tab === 'chat' && open) {
    await nextTick()
    scrollChatToBottom()
  }
})

function scrollChatToBottom() {
  const chatMessagesEl = document.querySelector('.chat-messages')
  if (chatMessagesEl) {
    chatMessagesEl.scrollTop = chatMessagesEl.scrollHeight
  }
}

function handleSelectNode(node: any) {
  selectNode({ node })
}

function handleOpenNodeEditor(payload: { node: any; rect: { left: number; top: number; width: number; height: number } }) {
  selectNode({ node: payload.node })
  const targetWidth = Math.min(540, window.innerWidth - 44)
  const targetHeight = Math.min(570, window.innerHeight - 92)
  editorMotion.value = {
    x: payload.rect.left + payload.rect.width / 2 - window.innerWidth / 2,
    y: payload.rect.top + payload.rect.height / 2 - window.innerHeight / 2,
    scaleX: Math.max(.18, Math.min(.7, payload.rect.width / targetWidth)),
    scaleY: Math.max(.16, Math.min(.7, payload.rect.height / targetHeight)),
  }
  panelOpen.value = false
  editorNode.value = payload.node
}

function closeCardEditor() {
  editorNode.value = null
  deselectNode()
}

async function handleEditorSave(payload: { content: string; name: string; color: string }) {
  if (!selectedNode.value) return
  const previousData = { ...selectedNode.value.data }
  selectedNode.value.data = { ...selectedNode.value.data, ...payload }
  const saved = await saveSelectedNode()
  if (saved) {
    closeCardEditor()
    showToast('卡片记录已保存。')
  } else {
    selectedNode.value.data = previousData
    showToast('保存失败，请稍后重试。')
  }
}

async function handleEditorDelete() {
  const deleted = await deleteSelectedNode(false)
  if (deleted) {
    closeCardEditor()
    showToast('卡片与关联线绳已移除。')
  }
}

function handleGoToCenter(vueFlowInstance: any) {
  goToCenter(vueFlowInstance)
}

function showToast(message: string) {
  toastMessage.value = message
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastMessage.value = '' }, 2400)
}

async function handleAddNote(payload: { type: string; position: { x: number; y: number } }) {
  const created = await addNote(payload.type, payload.position)
  if (created) showToast(payload.type === 'clue' ? '线索已固定到调查墙。' : '嫌疑人档案已固定到调查墙。')
}

async function handleDeleteNode(node: any) {
  selectNode({ node })
  await nextTick()
  const deleted = await deleteSelectedNode()
  if (deleted) showToast('卡片与关联线绳已移除。')
}

onMounted(async () => {
  await loadNotes()
  await loadConnections()
  await Promise.all([
    loadTimelineEvents(),
    loadChatHistory(),
    loadDocuments(),
    loadKnownInfos(),
  ])
  await nextTick()
  goToCenter()
})
</script>

<style scoped>
.case-detail {
  height: calc(100vh - 36px);
  min-height: 620px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--plaster);
  position: relative;
}

.main-area {
  flex: 1;
  display: flex;
  overflow: hidden;
  position: relative;
  padding: 14px 14px 14px 0;
  gap: 14px;
  background: var(--plaster);
}

.card-editor-overlay {
  position: fixed;
  z-index: 1200;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 24px;
  box-sizing: border-box;
  background: rgba(55, 43, 29, .2);
  isolation: isolate;
}
.card-editor-overlay-enter-active,
.card-editor-overlay-leave-active {
  transition: background-color 220ms ease-out, opacity 220ms ease-out;
}
.card-editor-overlay-enter-active :deep(.card-editor-card),
.card-editor-overlay-leave-active :deep(.card-editor-card) {
  transition: transform 300ms cubic-bezier(.32,.72,0,1), opacity 180ms ease-out, filter 220ms ease-out;
}
.card-editor-overlay-enter-from,
.card-editor-overlay-leave-to { opacity: 0; background: rgba(55,43,29,0); }
.card-editor-overlay-enter-from :deep(.card-editor-card),
.card-editor-overlay-leave-to :deep(.card-editor-card) {
  opacity: .3;
  filter: blur(.7px);
  transform:
    translate3d(var(--editor-origin-x), var(--editor-origin-y), 0)
    scale(var(--editor-origin-scale-x), var(--editor-origin-scale-y))
    rotate(.4deg);
}

.timeline-reveal {
  position: absolute;
  z-index: 25;
  top: 58px;
  left: 0;
  right: 0;
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
  transform: translate3d(0, -10px, 0);
  transition:
    transform 210ms cubic-bezier(.23,1,.32,1),
    opacity 140ms ease-out,
    visibility 0s linear 210ms;
  will-change: transform, opacity;
}

.timeline-reveal.open {
  opacity: 1;
  visibility: visible;
  pointer-events: auto;
  transform: translate3d(0, 0, 0);
  transition:
    transform 230ms cubic-bezier(.32,.72,0,1),
    opacity 150ms ease-out,
    visibility 0s;
}

.timeline-reveal-inner {
  overflow: visible;
  box-shadow: 0 18px 34px rgba(61,45,27,.16);
}

.case-toast {
  position: fixed;
  z-index: 2000;
  top: 70px;
  left: 50%;
  transform: translateX(-50%);
  padding: 11px 18px;
  border: 1px solid rgba(255, 255, 255, 0.28);
  border-radius: 999px;
  color: #f8f1e6;
  background: rgba(41, 36, 30, 0.94);
  box-shadow: 0 14px 32px rgba(35, 28, 19, 0.28);
  font-size: 13px;
  letter-spacing: 0.02em;
}

.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translate(-50%, -10px);
}

/* 滚动条美化 */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: var(--rust);
  border-radius: 3px;
}

@media (max-width: 900px) {
  .main-area {
    padding-right: 8px;
    gap: 8px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .timeline-reveal { transition-duration: .01ms; transform: none; }
}
</style>
