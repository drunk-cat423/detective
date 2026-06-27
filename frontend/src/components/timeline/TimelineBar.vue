<template>
  <div class="timeline-bar">
    <div style="display:flex; align-items:center; gap:12px;">
      <router-link to="/" class="back-btn">🏠︎</router-link>
      <span @click="$emit('update:open', !open)" class="timeline-toggle">
        ⏳ 时间线 {{ open ? '▲' : '▼' }}
      </span>
    </div>
    <button v-if="open" @click="$emit('toggle-add')">
      {{ showAdd ? '取消' : '+ 添加事件' }}
    </button>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  open: boolean
  showAdd: boolean
}>()

defineEmits<{
  'update:open': [value: boolean]
  'toggle-add': []
}>()
</script>

<style scoped>
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

.timeline-toggle {
  cursor: pointer;
  color: var(--white);
  font-weight: 600;
  font-size: 14px;
}
</style>
