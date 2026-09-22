<template>
  <aside ref="panelRootRef" class="side-panel" :class="{ collapsed: !open }">
    <button class="file-peek" aria-label="打开案件档案" @click="emit('update:open', true)">
      <span class="peek-tab">CASE FILE</span>
      <span class="peek-copy"><strong>案件档案</strong><small>点击调阅</small></span>
      <span class="peek-corner" aria-hidden="true"></span>
    </button>

    <div class="file-folder" :aria-hidden="!open">
      <button class="toggle-panel-btn" aria-label="收起案件档案" @click="emit('update:open', false)">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 7l10 10M17 7 7 17" /></svg>
      </button>
      <span class="clipboard-clip" aria-hidden="true"><i></i></span>

      <header class="folder-header">
        <div class="case-label">
          <span>PRIVATE INVESTIGATION</span>
          <strong>案件档案</strong>
          <small>CASE FILE · NO. 001</small>
        </div>
        <div class="classification"><span>STATUS</span><strong>调查中</strong></div>
      </header>

      <nav class="index-tabs" role="tablist" aria-label="案件档案分区" :aria-hidden="!open" @keydown="onTabKeydown">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          :ref="el => setTabRef(tab.key, el)"
          class="index-tab"
          :class="{ active: activeTab === tab.key }"
          role="tab"
          :tabindex="activeTab === tab.key ? 0 : -1"
          :aria-selected="activeTab === tab.key"
          @click="switchTab(tab.key)"
        >
          <span class="tab-index">{{ tab.mark }}</span>
          <span class="tab-label">{{ tab.label }}</span>
        </button>
      </nav>

      <div class="document-window" :aria-hidden="!open">
        <Transition :name="contentTransition">
          <section :key="activeTab" class="archive-page">
            <span class="section-stamp" :class="`stamp-${activeTab}`" aria-hidden="true">{{ activeMeta.stamp }}</span>
            <div class="section-heading">
              <div><span>{{ activeMeta.eyebrow }}</span><strong>{{ activeMeta.title }}</strong></div>
              <small>{{ activeMeta.mark }} / 03</small>
            </div>
            <div class="document-rule" aria-hidden="true"><i></i></div>
            <div ref="documentSheetRef" class="document-sheet"><slot /></div>
          </section>
        </Transition>
        <Transition name="continuation">
          <span v-if="canScrollDown" class="page-depth-fade" aria-hidden="true"></span>
        </Transition>
        <Transition name="continuation">
          <button v-if="canScrollDown" class="page-continuation" type="button" @click="scrollFurther">
            <span>继续查阅</span><i aria-hidden="true">↓</i>
          </button>
        </Transition>
      </div>
      <span class="folder-lip" aria-hidden="true"></span>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps<{ open: boolean; activeTab: string }>()
const emit = defineEmits<{
  'update:open': [value: boolean]
  'update:activeTab': [value: string]
}>()

const tabs = [
  { key: 'chat', label: '推理', mark: '01', eyebrow: 'ANALYSIS NOTES', title: '推理记录', stamp: '析' },
  { key: 'docs', label: '文档', mark: '02', eyebrow: 'SOURCE MATERIAL', title: '相关文档', stamp: '档' },
  { key: 'info', label: '事实', mark: '03', eyebrow: 'KNOWN FACTS', title: '已知事实', stamp: '实' },
]

const contentTransition = 'file-stack'
const panelRootRef = ref<HTMLElement | null>(null)
const tabRefs = new Map<string, HTMLButtonElement>()
const activeMeta = computed(() => tabs.find(tab => tab.key === props.activeTab) ?? tabs[0])
const documentSheetRef = ref<HTMLElement | null>(null)
const canScrollDown = ref(false)
let activeScroller: HTMLElement | null = null
let cueTimer: number | undefined
let contentObserver: MutationObserver | undefined
let sizeObserver: ResizeObserver | undefined

function setTabRef(key: string, el: unknown) {
  if (el instanceof HTMLButtonElement) tabRefs.set(key, el)
}

function switchTab(tab: string) {
  if (tab !== props.activeTab) {
    canScrollDown.value = false
    emit('update:activeTab', tab)
  }
}

function updateScrollCue() {
  const scroller = activeScroller
  canScrollDown.value = !!scroller && scroller.scrollHeight - scroller.clientHeight - scroller.scrollTop > 48
}

function unbindScroller() {
  activeScroller?.removeEventListener('scroll', updateScrollCue)
  activeScroller = null
  contentObserver?.disconnect()
  sizeObserver?.disconnect()
}

function bindScroller() {
  unbindScroller()
  const sheet = documentSheetRef.value
  if (!sheet) return
  activeScroller = props.activeTab === 'chat'
    ? sheet.querySelector<HTMLElement>('.chat-messages') ?? sheet
    : sheet
  activeScroller.addEventListener('scroll', updateScrollCue, { passive: true })
  contentObserver = new MutationObserver(updateScrollCue)
  contentObserver.observe(activeScroller, { childList: true, subtree: true, characterData: true })
  sizeObserver = new ResizeObserver(updateScrollCue)
  sizeObserver.observe(activeScroller)
  if (activeScroller.firstElementChild instanceof HTMLElement) sizeObserver.observe(activeScroller.firstElementChild)
  updateScrollCue()
}

async function scheduleScrollerBinding(delay = 0) {
  await nextTick()
  window.clearTimeout(cueTimer)
  cueTimer = window.setTimeout(bindScroller, delay)
}

function scrollFurther() {
  if (!activeScroller) return
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  activeScroller.scrollBy({ top: Math.max(180, activeScroller.clientHeight * .68), behavior: reducedMotion ? 'auto' : 'smooth' })
}

function closeWhenClickingOutside(event: PointerEvent) {
  if (!props.open) return
  const target = event.target
  if (target instanceof Node && !panelRootRef.value?.contains(target)) {
    emit('update:open', false)
  }
}

watch(() => props.activeTab, () => scheduleScrollerBinding(360))
watch(() => props.open, open => { if (open) scheduleScrollerBinding(300) })

onMounted(() => {
  document.addEventListener('pointerdown', closeWhenClickingOutside, true)
  scheduleScrollerBinding()
  window.setTimeout(updateScrollCue, 700)
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', closeWhenClickingOutside, true)
  window.clearTimeout(cueTimer)
  unbindScroller()
})

function onTabKeydown(event: KeyboardEvent) {
  if (!['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) return
  event.preventDefault()
  const current = tabs.findIndex(tab => tab.key === props.activeTab)
  let next = current
  if (event.key === 'ArrowDown') next = (current + 1) % tabs.length
  if (event.key === 'ArrowUp') next = (current - 1 + tabs.length) % tabs.length
  if (event.key === 'Home') next = 0
  if (event.key === 'End') next = tabs.length - 1
  switchTab(tabs[next].key)
  tabRefs.get(tabs[next].key)?.focus()
}
</script>

<style scoped>
.side-panel {
  --panel-width: 412px;
  --folder: #8f7955;
  --paper: #f2ecde;
  --file-ink: #332f28;
  --file-muted: #807767;
  --file-red: #95483f;
  position: absolute;
  z-index: 30;
  top: 52%;
  right: 68px;
  width: var(--panel-width);
  height: min(680px, calc(100% - 76px));
  overflow: visible;
  pointer-events: none;
  transform: translateY(-50%);
}

.file-folder {
  position: relative;
  isolation: isolate;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
  border: 1px solid rgba(70, 53, 31, .42);
  border-radius: 5px 10px 10px 5px;
  background: linear-gradient(90deg, rgba(67, 48, 28, .14), transparent 18px), repeating-linear-gradient(3deg, rgba(255, 255, 255, .018) 0 1px, transparent 1px 5px), var(--folder);
  box-shadow: 0 30px 68px rgba(40, 29, 17, .34), 0 7px 18px rgba(40, 29, 17, .18), inset 0 1px rgba(255, 255, 255, .18);
  opacity: 1;
  pointer-events: auto;
  transform: translate3d(-4px, -2px, 0) rotate(-.9deg) scale(1);
  transform-origin: right bottom;
  transition: transform 330ms cubic-bezier(.32, .72, 0, 1), opacity 120ms ease-out 40ms, visibility 0s;
  will-change: transform, opacity;
}
.file-folder::after {
  content: '';
  position: absolute;
  z-index: 0;
  top: 19px;
  right: 7px;
  bottom: 8px;
  left: 22px;
  border: 1px solid rgba(75, 58, 35, .22);
  border-radius: 2px 5px 3px 3px;
  background: #d8caaa;
  box-shadow: 4px 5px 10px rgba(45, 31, 15, .12);
  transform: translate(6px, 2px) rotate(1.15deg);
}
.side-panel.collapsed .file-folder {
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
  transform: translate3d(57px, -5px, 0) rotate(-2deg) scale(.355, .135);
  transition: transform 330ms cubic-bezier(.77, 0, .175, 1), opacity 90ms linear 230ms, visibility 0s linear 330ms;
}

.file-peek {
  position: absolute;
  z-index: 40;
  right: -57px;
  bottom: 5px;
  width: 146px;
  height: 92px;
  display: block;
  padding: 25px 14px 12px 18px;
  overflow: hidden;
  border: 1px solid rgba(62, 44, 24, .5);
  border-radius: 5px 0 0 7px;
  color: #332b20;
  text-align: left;
  background:
    linear-gradient(125deg, rgba(255,255,255,.2), transparent 40%),
    repeating-linear-gradient(4deg, rgba(255,255,255,.025) 0 1px, transparent 1px 5px),
    #9a8158;
  box-shadow: -10px 13px 28px rgba(40, 28, 14, .26), inset 0 1px rgba(255,255,255,.2);
  cursor: pointer;
  opacity: 1;
  pointer-events: auto;
  transform: translate3d(0, 0, 0) rotate(-2deg) scale(1);
  transform-origin: right bottom;
  transition: transform 150ms cubic-bezier(.23, 1, .32, 1), opacity 90ms ease-out 240ms, visibility 0s;
}
.side-panel:not(.collapsed) .file-peek {
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
  transform: translate3d(0, 0, 0) rotate(-2deg) scale(1);
  transition: opacity 70ms ease-out, visibility 0s linear 70ms;
}
.peek-tab { position: absolute; top: 0; left: 15px; height: 23px; padding: 0 12px; display: flex; align-items: center; border-radius: 4px 4px 0 0; color: rgba(255,246,228,.8); background: #705a3c; font: 7px var(--mono); letter-spacing: .16em; }
.peek-copy { display: flex; flex-direction: column; position: relative; z-index: 2; }
.peek-copy strong { color: #fff7e8; font: 600 18px/1.35 var(--serif); letter-spacing: .06em; }
.peek-copy small { color: rgba(255,247,231,.62); font: 8px/1.5 var(--mono); letter-spacing: .13em; }
.peek-corner { position: absolute; right: -1px; bottom: -1px; width: 35px; height: 35px; background: linear-gradient(135deg, rgba(75,55,31,.16) 49%, #c4ad82 51%); box-shadow: -2px -2px 5px rgba(62,45,26,.12); }
.file-peek:active { transform: rotate(-2deg) scale(.97); }
.file-folder::before {
  content: '';
  position: absolute;
  z-index: 1;
  inset: 14px 14px 13px;
  border: 1px solid rgba(67, 51, 30, .26);
  border-radius: 2px 4px 5px 2px;
  background: var(--paper);
  box-shadow: 0 5px 13px rgba(48, 34, 17, .16);
}

.folder-header {
  position: absolute;
  z-index: 4;
  top: 15px;
  right: 15px;
  left: 15px;
  height: 86px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 10px 58px;
  box-sizing: border-box;
  color: var(--file-ink);
  border-bottom: 1px solid rgba(75, 62, 44, .18);
  background: radial-gradient(ellipse at 18% 0, rgba(255, 255, 255, .5), transparent 42%), var(--paper);
  transition: opacity 100ms ease-out 150ms;
}
.case-label { display: flex; flex-direction: column; min-width: 0; }
.case-label > span { font: 7px var(--mono); letter-spacing: .19em; opacity: .68; }
.case-label strong { margin: 1px 0; font: 600 22px/1.2 var(--serif); letter-spacing: .06em; }
.case-label small { font: 7px var(--mono); letter-spacing: .13em; opacity: .6; }
.classification { display: flex; flex-direction: column; align-items: flex-end; padding-left: 15px; border-left: 1px solid rgba(78, 64, 44, .18); }
.classification span { font: 7px var(--mono); letter-spacing: .16em; opacity: .58; }
.classification strong { color: var(--file-red); font: 600 12px/1.8 var(--sans); letter-spacing: .08em; }

.toggle-panel-btn {
  position: absolute;
  z-index: 20;
  top: 38px;
  left: 28px;
  width: 31px;
  height: 31px;
  display: grid;
  place-items: center;
  padding: 0;
  border: 1px solid rgba(55, 40, 24, .34);
  border-radius: 50%;
  color: #3e3528;
  background: #c6b38e;
  box-shadow: 0 3px 8px rgba(47, 34, 18, .22), inset 0 1px rgba(255, 255, 255, .34);
  cursor: pointer;
  transition: transform 130ms cubic-bezier(.23, 1, .32, 1), background-color 130ms ease, opacity 80ms ease-out 150ms;
}
.toggle-panel-btn:active { transform: scale(.96); }
.toggle-panel-btn svg { width: 15px; height: 15px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.clipboard-clip {
  position: absolute;
  z-index: 15;
  top: -13px;
  left: 47%;
  width: 146px;
  height: 45px;
  border: 1px solid #332f2a;
  border-radius: 4px 4px 14px 14px;
  background:
    linear-gradient(90deg, transparent 12%, rgba(255,255,255,.3) 28%, transparent 38%),
    linear-gradient(180deg, #8c8a83 0%, #575650 44%, #2e2d2a 63%, #75736b 77%, #383733 100%);
  box-shadow: 0 5px 7px rgba(31, 24, 16, .34), inset 0 1px rgba(255,255,255,.38);
  transform: translateX(-50%) rotate(.8deg);
  transition: opacity 80ms ease-out 150ms;
}
.clipboard-clip::before, .clipboard-clip::after { content: ''; position: absolute; top: 8px; width: 15px; height: 15px; border-radius: 50%; background: radial-gradient(circle at 40% 35%, #b5b3aa 0 8%, #55534d 32%, #252421 72%); box-shadow: inset 0 1px rgba(255,255,255,.25); }
.clipboard-clip::before { left: 17px; }
.clipboard-clip::after { right: 17px; }
.clipboard-clip i { position: absolute; right: 31px; bottom: 6px; left: 31px; height: 5px; border-radius: 0 0 8px 8px; background: #282724; box-shadow: 0 1px rgba(255,255,255,.18); }

.document-window {
  position: absolute;
  z-index: 3;
  top: 101px;
  right: 15px;
  bottom: 15px;
  left: 15px;
  overflow: visible;
  border: 1px solid rgba(77, 61, 39, .3);
  border-radius: 2px 4px 5px 2px;
  color: var(--file-ink);
  background: radial-gradient(ellipse at 17% 2%, rgba(255, 255, 255, .5), transparent 32%), repeating-linear-gradient(0deg, rgba(88, 71, 47, .018) 0 1px, transparent 1px 4px), var(--paper);
  box-shadow: 0 7px 18px rgba(49, 35, 18, .17), inset 12px 0 18px rgba(91, 69, 40, .035);
  transform: translate(-1px, 1px) rotate(.28deg);
  transition: opacity 100ms ease-out 150ms, transform 160ms cubic-bezier(.23, 1, .32, 1), visibility 0s;
}
.document-window::before, .document-window::after {
  content: '';
  position: absolute;
  z-index: 0;
  right: 7px;
  bottom: 5px;
  left: 7px;
  height: 100%;
  border: 1px solid rgba(81, 63, 40, .15);
  background: #e7deca;
  pointer-events: none;
}
.document-window::before { transform: translate(3px, 3px) rotate(.35deg); }
.document-window::after { transform: translate(-2px, 5px) rotate(-.28deg); background: #ddd1b8; }
.archive-page {
  position: absolute;
  z-index: 2;
  inset: 0;
  overflow: hidden;
  background:
    radial-gradient(ellipse at 17% 2%, rgba(255, 255, 255, .5), transparent 32%),
    repeating-linear-gradient(0deg, rgba(88, 71, 47, .018) 0 1px, transparent 1px 4px),
    var(--paper);
  box-shadow: 0 2px 5px rgba(54, 39, 21, .1);
  transform-origin: 92% 88%;
  backface-visibility: hidden;
  will-change: transform, opacity;
}
.section-stamp {
  position: absolute;
  z-index: 7;
  top: 17px;
  left: 10px;
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  border: 2px solid rgba(144, 64, 54, .72);
  border-radius: 50%;
  color: rgba(144, 64, 54, .78);
  font: 700 15px/1 var(--serif);
  mix-blend-mode: multiply;
  opacity: .82;
  transform: rotate(var(--stamp-tilt, -7deg));
}
.section-stamp::before { content: ''; position: absolute; inset: 3px; border: 1px solid rgba(144, 64, 54, .54); border-radius: 50%; }
.section-stamp::after { content: ''; position: absolute; inset: -3px 5px; border-top: 1px solid rgba(144, 64, 54, .2); border-bottom: 1px solid rgba(144, 64, 54, .18); transform: rotate(18deg); }
.stamp-chat { --stamp-tilt: 5deg; }
.stamp-docs { --stamp-tilt: -3deg; }
.stamp-info { --stamp-tilt: 7deg; }
.section-heading { position: absolute; z-index: 5; inset: 0 0 auto; height: 70px; display: flex; align-items: flex-end; justify-content: space-between; padding: 15px 22px 10px 58px; box-sizing: border-box; background: linear-gradient(180deg, rgba(255, 255, 255, .2), transparent); }
.section-heading > div { display: flex; flex-direction: column; }
.section-heading span { color: var(--file-muted); font: 7px var(--mono); letter-spacing: .17em; }
.section-heading strong { font: 600 19px/1.35 var(--serif); letter-spacing: .055em; }
.section-heading small { padding-bottom: 3px; color: rgba(76, 68, 56, .45); font: 8px var(--mono); letter-spacing: .12em; }
.document-rule { position: absolute; z-index: 6; top: 69px; right: 21px; left: 58px; height: 5px; border-top: 1px solid rgba(75, 62, 44, .19); }
.document-rule i { display: block; width: 60px; margin-top: -2px; border-top: 3px solid var(--file-red); transform: rotate(-1deg); }
.document-sheet { position: absolute; z-index: 2; inset: 75px 0 0; overflow: auto; padding: 14px 10px 34px 34px; box-sizing: border-box; scrollbar-width: none; }
.document-sheet :deep(.chat-messages) { scrollbar-width: none; }
.document-sheet::-webkit-scrollbar,
.document-sheet :deep(.chat-messages::-webkit-scrollbar) { display: none; width: 0; height: 0; }

.page-depth-fade { position: absolute; z-index: 7; right: 0; bottom: 0; left: 0; height: 72px; pointer-events: none; background: linear-gradient(180deg, transparent, rgba(242, 236, 222, .84) 62%, var(--paper)); }
.page-continuation {
  position: absolute;
  z-index: 9;
  right: 24px;
  bottom: 13px;
  min-width: 88px;
  height: 31px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 0 12px 0 14px;
  border: 0;
  color: rgba(91, 62, 43, .82);
  background:
    repeating-linear-gradient(2deg, rgba(99, 73, 48, .035) 0 1px, transparent 1px 4px),
    #e8dcc2;
  box-shadow: 0 4px 9px rgba(62, 43, 23, .14), inset 0 1px rgba(255, 255, 255, .45);
  clip-path: polygon(2% 7%, 97% 0, 100% 84%, 93% 100%, 4% 93%, 0 18%);
  cursor: pointer;
  transform: rotate(-1.4deg);
  transition: transform 150ms cubic-bezier(.23, 1, .32, 1), color 140ms ease, background-color 140ms ease;
}
.page-continuation span { font: 11px var(--serif); letter-spacing: .09em; }
.page-continuation i { color: var(--file-red); font: 700 14px/1 var(--sans); font-style: normal; }
.page-continuation:active { transform: rotate(-1.4deg) scale(.97); }
.page-continuation:focus-visible { outline: 2px solid rgba(149, 72, 63, .65); outline-offset: 3px; }
.continuation-enter-active, .continuation-leave-active { transition: opacity 160ms ease-out, transform 180ms cubic-bezier(.23, 1, .32, 1); }
.continuation-enter-from, .continuation-leave-to { opacity: 0; transform: translateY(6px); }
.folder-lip { position: absolute; z-index: 2; right: 5px; bottom: 5px; left: 5px; height: 8px; border-radius: 0 0 7px 4px; background: linear-gradient(180deg, rgba(73, 53, 30, .08), rgba(54, 39, 22, .18)); pointer-events: none; transition: opacity 80ms ease-out 150ms; }

.index-tabs { position: absolute; z-index: 2; top: 140px; left: calc(100% - 30px); display: flex; flex-direction: column; gap: 3px; transition: opacity 100ms ease-out 150ms, transform 160ms cubic-bezier(.23, 1, .32, 1), visibility 0s; }
.index-tab { position: relative; width: 64px; height: 47px; display: flex; flex-direction: column; align-items: flex-start; justify-content: center; gap: 1px; padding: 0 7px 0 22px; overflow: hidden; border: 1px solid rgba(76, 60, 39, .28); border-left: 0; border-radius: 1px 6px 5px 1px; color: #554b3c; background: linear-gradient(96deg, #b9ab8e 0 16px, #d5c9ae 17px 100%); box-shadow: 2px 2px 4px rgba(45, 32, 17, .14), inset 0 1px rgba(255, 255, 255, .28); cursor: pointer; transform-origin: left center; transform: translateX(var(--tab-shift, 0px)) rotate(var(--tab-tilt, 0deg)); transition: transform 210ms cubic-bezier(.23, 1, .32, 1), color 190ms ease, background-color 190ms ease, filter 190ms ease; }
.index-tab::after { content: ''; position: absolute; inset: 2px; opacity: .18; pointer-events: none; background: repeating-linear-gradient(3deg, rgba(83, 65, 42, .13) 0 1px, transparent 1px 4px); }
.index-tab:nth-child(1) { --tab-tilt: .18deg; --tab-shift: 1px; }
.index-tab:nth-child(2) { --tab-tilt: -.22deg; --tab-shift: 0px; background: linear-gradient(96deg, #b5a78a 0 16px, #d1c4a9 17px 100%); }
.index-tab:nth-child(3) { --tab-tilt: .12deg; --tab-shift: 2px; background: linear-gradient(96deg, #b9aa8d 0 16px, #d7cbb1 17px 100%); }
.index-tab:nth-child(4) { --tab-tilt: -.28deg; --tab-shift: 1px; background: linear-gradient(96deg, #b2a487 0 16px, #cec1a6 17px 100%); }
.tab-index { position: relative; z-index: 1; color: #8b7e68; font: 7px var(--mono); letter-spacing: .12em; }
.tab-label { position: relative; z-index: 1; font: 600 12px var(--serif); letter-spacing: .08em; }
.index-tab.active { color: #fff5e7; background: linear-gradient(100deg, #723c37 0 16px, #994d44 17px, #8b423b 100%); filter: saturate(.9); transform: translateX(calc(5px + var(--tab-shift, 0px))) rotate(var(--tab-tilt, 0deg)); }
.index-tab.active .tab-index { color: rgba(255, 245, 231, .66); }
.index-tab:active { transform: translateX(calc(2px + var(--tab-shift, 0px))) rotate(var(--tab-tilt, 0deg)) scale(.97); }
.index-tab.active:active { transform: translateX(calc(5px + var(--tab-shift, 0px))) rotate(var(--tab-tilt, 0deg)) scale(.97); }
.index-tab:focus-visible { outline: 2px solid #fff7e7; outline-offset: 2px; }

.file-stack-enter-active {
  z-index: 2;
  transition: transform 310ms cubic-bezier(.23, 1, .32, 1), opacity 210ms ease-out, filter 210ms ease-out;
}
.file-stack-leave-active {
  z-index: 4;
  pointer-events: none;
  transition: transform 330ms cubic-bezier(.65, 0, .25, 1), opacity 100ms linear 230ms, filter 140ms ease-out 185ms;
}
.file-stack-enter-from {
  opacity: .7;
  filter: brightness(.94) blur(.25px);
  transform: translate3d(10px, 7px, 0) rotate(.6deg) scale(.988);
}
.file-stack-leave-to {
  opacity: 0;
  filter: blur(1px) brightness(.96);
  transform: translate3d(-76%, 22px, 0) rotate(-4deg) scale(.982);
}

.document-sheet :deep(> .panel-content) { min-height: calc(100% - 48px); box-sizing: border-box; }
.document-sheet :deep(> .chat-panel) { height: calc(100% - 48px); }
.document-sheet :deep(.edit-field), .document-sheet :deep(.color-picker) { padding-right: 12px; padding-left: 4px; }
.document-sheet :deep(.edit-field label) { color: var(--file-ink); font-family: var(--serif); font-size: 13px; letter-spacing: .04em; }
.document-sheet :deep(textarea), .document-sheet :deep(input) { border: 1px solid rgba(96, 78, 52, .26); border-radius: 3px; background: rgba(255, 253, 247, .68); box-shadow: inset 0 1px 3px rgba(68, 51, 31, .045); transition: border-color 130ms ease, box-shadow 130ms ease, background-color 130ms ease; }
.document-sheet :deep(textarea:focus), .document-sheet :deep(input:focus) { border-color: rgba(149, 72, 63, .62); box-shadow: 0 0 0 2px rgba(149, 72, 63, .11); background: #fffdf8; }
.document-sheet :deep(.color-swatch) { width: 24px; height: 24px; border-width: 2px; box-shadow: 0 1px 3px rgba(46, 34, 19, .14); transition: transform 130ms cubic-bezier(.23, 1, .32, 1), box-shadow 130ms ease; }
.document-sheet :deep(.color-swatch.active) { border-color: var(--file-red); box-shadow: 0 0 0 2px rgba(149, 72, 63, .13); }
.document-sheet :deep(.edit-btn), .document-sheet :deep(.known-info-button) { border-radius: 3px; transition: transform 130ms cubic-bezier(.23, 1, .32, 1), background-color 130ms ease, box-shadow 130ms ease; }
.document-sheet :deep(.save-btn), .document-sheet :deep(.known-info-button) { border-color: #773d37; color: #fff8ee; background: var(--file-red); box-shadow: 0 2px 5px rgba(88, 45, 39, .18); }
.document-sheet :deep(.edit-btn:active), .document-sheet :deep(.known-info-button:active) { transform: scale(.97); }
.document-sheet :deep(.chat-messages) { background: transparent; }
.document-sheet :deep(.chat-input) { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 7px; padding: 10px 12px 4px 4px; border-top: 1px solid rgba(77, 62, 42, .2); background: rgba(247, 242, 231, .76); }
.document-sheet :deep(.chat-input::before) { display: none; }
.document-sheet :deep(.chat-input input) { grid-column: 1 / -1; width: 100%; min-width: 0; box-sizing: border-box; }
.document-sheet :deep(.chat-input button) { min-width: 0; margin: 0; padding: 7px 5px; border-radius: 3px; }
.document-sheet :deep(.upload-area) { margin-right: 10px; border: 1px dashed rgba(111, 90, 58, .48); border-radius: 3px; background: rgba(255, 253, 247, .36); transition: transform 140ms cubic-bezier(.23, 1, .32, 1), border-color 120ms ease, background-color 120ms ease; }
.document-sheet :deep(.doc-list), .document-sheet :deep(.known-info-list li), .document-sheet :deep(.info-content) { border-radius: 3px; background: rgba(255, 253, 247, .62); }
.document-sheet :deep(.info-hint) { border-radius: 2px; border-left-color: var(--file-red); background: rgba(149, 72, 63, .08); color: #70443e; }

.side-panel.collapsed .toggle-panel-btn,
.side-panel.collapsed .clipboard-clip,
.side-panel.collapsed .folder-header,
.side-panel.collapsed .document-window,
.side-panel.collapsed .index-tabs,
.side-panel.collapsed .folder-lip {
  opacity: 0;
  pointer-events: none;
  transition-delay: 0ms;
}

@media (hover: hover) and (pointer: fine) {
  .toggle-panel-btn:hover { background: #dac8a3; transform: scale(1.04); }
  .file-peek:hover { transform: translate3d(-8px, -5px, 0) rotate(-1deg) scale(1.015); }
  .index-tab:hover:not(.active) { filter: brightness(1.045) saturate(.92); }
  .document-sheet :deep(.color-swatch:hover) { transform: scale(1.12); }
}
@media (max-width: 900px) {
  .side-panel { --panel-width: min(390px, calc(100vw - 70px)); right: 52px; height: min(640px, calc(100% - 62px)); }
  .folder-header { padding-right: 15px; }
  .classification { display: none; }
  .document-sheet { padding-left: 22px; }
  .section-heading { padding-left: 52px; }
  .document-rule { left: 52px; }
}
@media (prefers-reduced-motion: reduce) {
  .file-folder, .file-peek, .toggle-panel-btn, .index-tabs, .index-tab, .document-window, .file-stack-enter-active, .file-stack-leave-active { transition-duration: .01ms; }
  .file-stack-enter-from, .file-stack-leave-to { transform: none; filter: none; }
}
</style>
