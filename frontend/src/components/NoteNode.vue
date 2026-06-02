<template>
  <div class="note-node" :style="{ background: data.color }">
    <Handle type="source" :position="Position.Top" id="source-top" />
    <Handle type="target" :position="Position.Top" id="target-top" />

    <div class="note-header">
      <span class="note-type">
        {{ data.type === 'clue' ? '🔍 线索' : '👤 嫌疑人' }}
      </span>
      <span v-if="data.type === 'suspect' && data.name" class="note-name">
        {{ data.name }}
      </span>
    </div>
    <div class="note-content">
      <p>{{ data.content }}</p>
    </div>

    <Handle type="source" :position="Position.Bottom" id="source-bottom" />
    <Handle type="target" :position="Position.Bottom" id="target-bottom" />
  </div>
</template>

<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'

defineProps<{
  id: string
  data: {
    content: string
    type: string
    color: string
    name?: string   // 新增可选属性
  }
}>()
</script>

<style scoped>
.note-node {
  width: 200px;
  min-height: 100px;
  padding: 10px;
  border-radius: 4px;
  box-shadow: 2px 2px 6px rgba(0, 0, 0, 0.15);
  font-size: 14px;
  cursor: pointer;
}
.note-header {
  margin-bottom: 6px;
  font-weight: bold;
  display: flex;
  align-items: center;
}
.note-type {
  white-space: nowrap;
}
.note-name {
  font-size: 13px;
  color: #333;
  font-weight: bold;
  margin-left: 6px;
}
.note-content p {
  margin: 0;
  white-space: pre-wrap;
}

/* Handle 样式保持不变 */
:deep(.vue-flow__handle) {
  width: 24px !important;
  height: 24px !important;
  background: transparent !important;
  border: none !important;
  border-radius: 0;
  box-shadow: none !important;
}
:deep(.vue-flow__handle-top) {
  top: -12px !important;
}
:deep(.vue-flow__handle-bottom) {
  bottom: -12px !important;
}
:deep(.vue-flow__handle::after) {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 16px;
  height: 16px;
  margin: -8px 0 0 -8px;
  background: #fff;
  border: 2px solid #666;
  border-radius: 50%;
  box-shadow: 0 0 8px rgba(0, 0, 0, 0.3);
  transition: transform 0.2s, box-shadow 0.2s;
}
:deep(.vue-flow__handle:hover::after) {
  transform: scale(1.3);
  box-shadow: 0 0 12px rgba(0, 0, 0, 0.5);
}
</style>