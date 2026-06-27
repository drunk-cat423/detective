<template>
  <div class="case-detail">
    <!-- 顶部时间线 -->
    <TimelineBar
      v-model:open="timelineOpen"
      :show-add="showAddEvent"
      @toggle-add="showAddEvent = !showAddEvent"
    />

    <!-- 时间线内容区 -->
    <TimelinePanel
      v-if="timelineOpen"
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

    <!-- 主区域 -->
    <div class="main-area">
      <!-- 便签墙画布 -->
      <NoteCanvas
        v-model:nodes="nodes"
        v-model:edges="edges"
        v-model:vueFlowRef="vueFlowRef"
        v-model:edgeEditInput="edgeEditInput"
        :editing-edge-for-label="editingEdgeForLabel"
        v-model:edit-edge-label-text="editEdgeLabelText"
        :edit-edge-position="editEdgePosition"
        :default-edge-options="defaultEdgeOptions"
        @select-node="handleSelectNode"
        @deselect-node="deselectNode"
        @go-to-center="handleGoToCenter"
        @on-connect="onConnect"
        @on-nodes-change="onNodesChange"
        @on-edge-double-click="onEdgeDoubleClick"
        @save-edge-label-edit="saveEdgeLabelEdit"
        @delete-current-edge="deleteCurrentEdge"
        @add-note="addNote"
      />

      <!-- 右侧面板 -->
      <SidePanel
        v-model:open="panelOpen"
        v-model:activeTab="activeTab"
      >
        <!-- 编辑 Tab -->
        <EditTab
          v-if="activeTab === 'edit'"
          :node="selectedNode"
          :preset-colors="presetColors"
          @save="saveSelectedNode"
          @delete="deleteSelectedNode"
          @update-node-data="handleUpdateNodeData"
        />

        <!-- 对话 Tab -->
        <ChatTab
          v-else-if="activeTab === 'chat'"
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'

import TimelineBar from '@/components/timeline/TimelineBar.vue'
import TimelinePanel from '@/components/timeline/TimelinePanel.vue'
import NoteCanvas from '@/components/canvas/NoteCanvas.vue'
import SidePanel from '@/components/sidebar/SidePanel.vue'
import EditTab from '@/components/sidebar/EditTab.vue'
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
const panelOpen = ref(true)
const activeTab = ref<'edit' | 'chat' | 'docs' | 'info'>('edit')

// Notes composable
const {
  nodes, edges, selectedNode, vueFlowRef, presetColors,
  editingEdgeForLabel, editEdgeLabelText, editEdgePosition, edgeEditInput, defaultEdgeOptions,
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
  loadDocuments, triggerFileInput, handleFileSelect, handleDrop,
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

function handleUpdateNodeData(field: string, value: any) {
  if (selectedNode.value) {
    selectedNode.value.data[field] = value
  }
}

function handleSelectNode(node: any) {
  selectNode({ node })
  activeTab.value = 'edit'
  panelOpen.value = true
}

function handleGoToCenter(vueFlowInstance: any) {
  goToCenter(vueFlowInstance)
}

onMounted(async () => {
  await Promise.all([
    loadNotes(),
    loadConnections(),
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

.main-area {
  flex: 1;
  display: flex;
  overflow: hidden;
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
</style>
