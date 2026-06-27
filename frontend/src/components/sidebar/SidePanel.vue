<template>
  <div class="side-panel" :class="{ collapsed: !open }">
    <div class="panel-header">
      <button class="toggle-panel-btn" @click="$emit('update:open', !open)">
        {{ open ? '▶' : '◀' }}
      </button>
      <div v-show="open" class="tab-buttons">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          :class="{ active: activeTab === tab.key }"
          @click="$emit('update:activeTab', tab.key)"
        >
          {{ tab.label }}
        </button>
      </div>
    </div>

    <div v-show="open" class="panel-content">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  open: boolean
  activeTab: string
}>()

defineEmits<{
  'update:open': [value: boolean]
  'update:activeTab': [value: string]
}>()

const tabs = [
  { key: 'edit', label: '编辑' },
  { key: 'chat', label: '对话' },
  { key: 'docs', label: '文档' },
  { key: 'info', label: '已知信息' },
]
</script>

<style scoped>
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

.panel-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  box-sizing: border-box;
  width: 100%;
}
</style>
