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
    <div class="timeline-actions">
      <Transition name="timeline-action">
        <button v-if="open" class="record-event-btn" :class="{ recording: showAdd }" :aria-label="showAdd ? '取消记录事件' : '记录事件'" @click="emit('toggle-add')">
          {{ showAdd ? '取消记录' : '＋ 记录事件' }}
        </button>
      </Transition>
      <div ref="searchAreaRef" class="case-search" :class="{ open: searchOpen }">
        <button
          class="search-trigger"
          type="button"
          aria-label="搜索线索或嫌疑人"
          :aria-expanded="searchOpen"
          @click="toggleSearch"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6"/><path d="m16 16 4 4"/></svg>
          <i v-if="searchQuery" class="search-active-mark" aria-hidden="true"></i>
        </button>
        <label class="search-box">
          <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6"/><path d="m16 16 4 4"/></svg>
          <input
            ref="searchInput"
            :value="searchQuery"
            placeholder="搜索线索或嫌疑人"
            aria-label="搜索线索或嫌疑人"
            @input="emit('update:searchQuery', ($event.target as HTMLInputElement).value)"
            @keydown.esc="closeSearch"
          />
          <kbd>Ctrl K</kbd>
        </label>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

defineProps<{
  open: boolean
  showAdd: boolean
  searchQuery: string
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  'toggle-add': []
  'update:searchQuery': [value: string]
}>()

const searchAreaRef = ref<HTMLElement | null>(null)
const searchInput = ref<HTMLInputElement | null>(null)
const searchOpen = ref(false)

async function focusSearch() {
  searchOpen.value = true
  await nextTick()
  searchInput.value?.focus()
}

function toggleSearch() {
  if (searchOpen.value) {
    closeSearch()
  } else {
    focusSearch()
  }
}

function closeSearch() {
  searchOpen.value = false
  searchInput.value?.blur()
}

function onShortcut(event: KeyboardEvent) {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
    event.preventDefault()
    focusSearch()
  }
}

function onOutsidePointerDown(event: PointerEvent) {
  if (searchOpen.value && event.target instanceof Node && !searchAreaRef.value?.contains(event.target)) {
    searchOpen.value = false
  }
}

onMounted(() => {
  window.addEventListener('keydown', onShortcut)
  document.addEventListener('pointerdown', onOutsidePointerDown, true)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onShortcut)
  document.removeEventListener('pointerdown', onOutsidePointerDown, true)
})
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
  z-index: 40;
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

.timeline-actions { display:flex; align-items:center; gap:12px; min-width:0; margin-left:auto; }
.case-search { position:relative; flex:0 0 250px; min-width:0; }
.search-box { height:35px; display:flex; align-items:center; gap:8px; box-sizing:border-box; padding:0 10px; border:1px solid rgba(89,68,43,.22); border-radius:3px 9px 5px 3px; color:var(--ink-soft); background:linear-gradient(105deg,rgba(255,255,255,.42),transparent 60%),#e9dfcb; box-shadow:inset 0 1px rgba(255,255,255,.48),0 2px 5px rgba(71,50,27,.08); }
.search-box svg,.search-trigger svg { width:16px; height:16px; flex:0 0 auto; fill:none; stroke:currentColor; stroke-width:1.8; stroke-linecap:round; }
.search-box input { flex:1; min-width:0; border:0; outline:0; color:var(--ink); background:transparent; font-size:12px; }
.search-box input::placeholder { color:var(--ink-faint); }
.search-box:focus-within { border-color:rgba(149,72,63,.64); box-shadow:0 0 0 2px rgba(149,72,63,.1); }
.search-box kbd { color:var(--ink-faint); font:9px var(--mono); white-space:nowrap; }
.search-trigger { display:none; }

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
  white-space: nowrap;
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
  .record-event-btn { width:36px; height:36px; flex:0 0 36px; padding:0; border-radius:50%; font-size:0; }
  .record-event-btn::before { content:'＋'; font:20px/1 var(--serif); }
  .record-event-btn.recording::before { content:'×'; font-size:22px; }
}

@media (max-width: 900px) {
  .timeline-actions { gap:8px; }
  .case-search { flex:0 0 36px; }
  .search-trigger { position:relative; width:36px; height:36px; display:grid; place-items:center; padding:0; border:1px solid var(--line); border-radius:50%; color:var(--ink-soft); background:rgba(255,255,255,.38); cursor:pointer; }
  .search-active-mark { position:absolute; right:3px; bottom:3px; width:5px; height:5px; border-radius:50%; background:var(--rust); }
  .search-box { position:absolute; z-index:2; top:44px; right:0; width:min(280px,calc(100vw - 22px)); height:42px; visibility:hidden; opacity:0; pointer-events:none; transform:translateY(-6px); transition:opacity 140ms ease-out,transform 180ms cubic-bezier(.23,1,.32,1),visibility 0s linear 180ms; box-shadow:0 9px 20px rgba(59,42,23,.18),inset 0 1px rgba(255,255,255,.48); }
  .case-search.open .search-box { visibility:visible; opacity:1; pointer-events:auto; transform:translateY(0); transition:opacity 140ms ease-out,transform 180ms cubic-bezier(.23,1,.32,1),visibility 0s; }
  .search-box kbd { display:none; }
}

@media (prefers-reduced-motion: reduce) {
  .timeline-toggle svg,
  .timeline-action-enter-active,
  .timeline-action-leave-active { transition-duration: .01ms; }
  .search-box { transition-duration:.01ms; }
}
</style>
