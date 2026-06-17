<template>
  <div class="note-node" :style="{ background: data.color }" :data-type="data.type">
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
  padding: 16px;
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08), 0 0 1px rgba(0, 0, 0, 0.1);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
  border: 2px solid transparent;
}

/* 线索类型默认渐变 - 仅当用户未手动设置颜色时生效 */
.note-node[data-type="clue"]:not([style*="background"]) {
  background: linear-gradient(135deg, #FFF8DC, #FFFACD);
  border: 1px solid #F0E6C8;
  transform: rotate(-1deg);
}

/* 嫌疑人类型默认渐变 - 仅当用户未手动设置颜色时生效 */
.note-node[data-type="suspect"]:not([style*="background"]) {
  background: linear-gradient(135deg, #FFE4E1, #FFF0F0);
  border: 1px solid #F0D0D0;
  transform: rotate(1deg);
}

.note-node:hover {
  transform: translateY(-4px) rotate(0deg) !important;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.15);
  border-color: #FFD700;
  z-index: 10;
}

/* 左上角装饰小星星 */
.note-node::before {
  content: '✦';
  position: absolute;
  top: 6px;
  right: 10px;
  font-size: 14px;
  color: #DAA520;
  opacity: 0.4;
}

.note-header {
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.note-type {
  white-space: nowrap;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  padding: 3px 10px;
  border-radius: 12px;
  background: rgba(255, 215, 0, 0.2);
  color: #B8860B;
}

.note-name {
  font-size: 14px;
  color: #2D2D2D;
  font-weight: 700;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.note-content p {
  margin: 0;
  white-space: pre-wrap;
  line-height: 1.6;
  color: #4A4A4A;
  font-size: 13px;
}

/* Handle 样式 - 金色主题 */
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
  border: 2px solid #FFD700;
  border-radius: 50%;
  box-shadow: 0 0 8px rgba(255, 215, 0, 0.4);
  transition: all 0.2s;
}

:deep(.vue-flow__handle:hover::after) {
  transform: scale(1.3);
  box-shadow: 0 0 12px rgba(255, 215, 0, 0.6);
  border-color: #DAA520;
}
</style>