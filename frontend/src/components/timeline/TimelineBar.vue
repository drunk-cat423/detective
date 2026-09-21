<template>
  <div class="timeline-bar">
    <div class="timeline-left">
      <router-link to="/" class="back-btn" aria-label="返回案件列表">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m14 6-6 6 6 6"/></svg>
      </router-link>
      <span class="product-mark">DETECTIVE<span>·</span></span>
      <i></i>
      <button
        class="timeline-toggle"
        :class="{ open }"
        :aria-expanded="open"
        aria-controls="case-timeline"
        @click="$emit('update:open', !open)"
      >
        <span>调查时间线 <small>{{ open ? '收起' : '展开' }}</small></span>
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m7 10 5 5 5-5"/></svg>
      </button>
    </div>
    <Transition name="timeline-action">
      <button v-if="open" class="record-event-btn" @click="$emit('toggle-add')">
        {{ showAdd ? '取消记录' : '＋ 记录事件' }}
      </button>
    </Transition>
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
  height: 58px;
  background: var(--paper);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 18px;
  border-bottom: 1px solid var(--line);
  position: relative;
  z-index: 10;
  flex-shrink: 0;
}

.timeline-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.timeline-left > i {
  height: 20px;
  width: 1px;
  background: var(--line);
}

.product-mark {
  color: var(--ink);
  font-family: var(--serif);
  font-size: 17px;
  font-style: normal;
  font-weight: 700;
  letter-spacing: .03em;
}

.product-mark span { color: var(--rust); }

.timeline-toggle small {
  margin-left: 7px;
  color: var(--ink-faint);
  font: 8px var(--mono);
  letter-spacing: .08em;
  text-transform: uppercase;
}

.record-event-btn {
  padding: 6px 14px;
  background: var(--ink);
  border: 1px solid var(--ink);
  border-radius: 999px;
  color: #f8f1e6;
  font-weight: 600;
  font-size: 13px;
  cursor: pointer;
  outline: none;
  transition: transform 140ms cubic-bezier(.23,1,.32,1), background 160ms ease, border-color 160ms ease;
  white-space: nowrap;
}
.record-event-btn:hover {
  background: var(--rust-dark);
  border-color: var(--rust-dark);
  transform: translateY(-1px);
}
.record-event-btn:active { transform: translateY(0) scale(.97); }

.back-btn {
  color: var(--ink-soft);
  text-decoration: none;
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  border: 1px solid var(--line);
  background: rgba(255,255,255,.4);
  transition: transform .2s ease, background .2s ease;
}

.back-btn svg { width: 18px; fill: none; stroke: currentColor; stroke-width: 1.8; }

.back-btn:hover {
  background: var(--white);
  transform: translateX(-2px);
}

.timeline-toggle {
  cursor: pointer;
  color: var(--ink-soft);
  font-weight: 600;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 7px 8px;
  margin-left: -8px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  transition: color 160ms ease, background 160ms ease, transform 140ms cubic-bezier(.23,1,.32,1);
}

.timeline-toggle:hover { color: var(--ink); background: rgba(91,70,45,.06); }
.timeline-toggle:active { transform: scale(.98); }
.timeline-toggle svg {
  width: 15px;
  height: 15px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  transition: transform 220ms cubic-bezier(.32,.72,0,1);
}
.timeline-toggle.open svg { transform: rotate(180deg); }

.timeline-action-enter-active,
.timeline-action-leave-active { transition: opacity 130ms ease-out, transform 180ms cubic-bezier(.23,1,.32,1); }
.timeline-action-enter-from,
.timeline-action-leave-to { opacity: 0; transform: translateY(-4px) scale(.97); }

@media (max-width: 560px) {
  .timeline-bar { padding: 0 10px; }
  .timeline-left { gap: 8px; }
  .timeline-left > i { display: none; }
  .product-mark { font-size: 14px; }
  .timeline-toggle { font-size: 13px; }
  .timeline-toggle small { display: none; }
  .record-event-btn { padding: 6px 10px; font-size: 12px; }
}

@media (prefers-reduced-motion: reduce) {
  .timeline-toggle svg,
  .timeline-action-enter-active,
  .timeline-action-leave-active { transition-duration: .01ms; }
}
</style>
