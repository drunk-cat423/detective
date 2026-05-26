<template>
  <div class="note-node" :style="{ background: data.color }">
    <Handle type="source" :position="Position.Top" id = "source-top" />
    <Handle type="target" :position="Position.Top" id = 'target-top' />
    <div class="note-header">
      <span class="note-type">{{ data.type === 'clue' ? '🔍 线索' : '👤 嫌疑人' }}</span>
    </div>
    <div class="note-content" @dblclick="startEdit">
      <p v-if="!editing">{{ data.content }}</p>
      <textarea
        v-else
        v-model="editContent"
        @blur="saveEdit"
        @keyup.escape="cancelEdit"
        rows="3"
      ></textarea>
    </div>
    <Handle type="source" :position="Position.Bottom" id = "source-bottom"/>
    <Handle type="target" :position="Position.Bottom" id = "target-bottom"/>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useVueFlow } from '@vue-flow/core'
import {Handle,Position} from '@vue-flow/core'

const props = defineProps<{
  id: string
  data: {
    content: string
    type: string
    color: string
  }
}>()

const { updateNodeData } = useVueFlow()
const editing = ref(false)
const editContent = ref(props.data.content)

function startEdit() {
  editing.value = true
  editContent.value = props.data.content
}

function saveEdit() {
  editing.value = false
  if (editContent.value !== props.data.content) {
    updateNodeData(props.id, { ...props.data, content: editContent.value })
  }
}

function cancelEdit() {
  editing.value = false
  editContent.value = props.data.content
}
</script>

<style scoped>
.note-node {
  width: 200px;
  min-height: 100px;
  padding: 10px;
  border-radius: 4px;
  box-shadow: 2px 2px 6px rgba(0,0,0,0.15);
  font-size: 14px;
  cursor: pointer;
}
.note-header {
  margin-bottom: 6px;
  font-weight: bold;
}
.note-content p {
  margin: 0;
  white-space: pre-wrap;
}
textarea {
  width: 100%;
  resize: vertical;
  font-size: 13px;
}

:deep(.vue-flow__handle) {
  width: 24px !important;
  height: 24px !important;
  background: transparent !important;
  border: none !important;
  border-radius: 0;
  box-shadow: none !important;
}

/* 上方手柄位置微调（向外偏移） */
:deep(.vue-flow__handle-top) {
  top: -12px !important;
}

/* 下方手柄位置微调 */
:deep(.vue-flow__handle-bottom) {
  bottom: -12px !important;
}

/* 用 ::after 伪元素画出真正的圆点 */
:deep(.vue-flow__handle::after) {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 13px;
  height: 13px;
  margin: -8px 0 0 -8px;          /* 居中 */
  background: #fff;
  border-radius: 50%;
  box-shadow: 0 0 8px rgba(0, 0, 0, 0.3);   /* 虚化光晕 */
  transition: transform 0.2s, box-shadow 0.2s;
}

/* 悬停时伪元素放大 + 加强光晕 */
:deep(.vue-flow__handle:hover::after) {
  transform: scale(1.3);
  box-shadow: 0 0 12px rgba(0, 0, 0, 0.5);
}
</style>