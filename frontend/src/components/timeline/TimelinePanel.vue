<template>
  <section ref="panelElement" class="timeline-panel" aria-label="案件时间线">
    <Teleport to="body">
      <div v-if="showForm" class="event-editor-overlay" @click.self="$emit('cancel-record')">
        <form ref="editorForm" class="event-editor" role="dialog" aria-modal="true" aria-labelledby="event-editor-title" @submit.prevent="$emit('submit')" @keydown="onEditorKeydown">
          <button class="event-editor-close" type="button" aria-label="关闭事件记录" @click="$emit('cancel-record')"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 6 12 12M6 18 18 6"/></svg></button>
          <header class="event-editor-heading"><span>事件记录</span><h2 id="event-editor-title">记录这一刻</h2></header>
          <fieldset class="event-date-field"><legend>发生时间</legend>
      <div class="datetime-picker" aria-label="事件时间" @input="advanceTimeField" @focusin="selectTimeField">
        <input type="number" v-model.number="eventYear" aria-label="年" min="1" max="9999" @change="fixDate" /><span>年</span>
        <input type="number" v-model.number="eventMonth" aria-label="月" min="1" max="12" @change="fixDate" /><span>月</span>
        <input type="number" v-model.number="eventDay" aria-label="日" min="1" max="31" @change="fixDate" /><span>日</span>
        <input type="number" v-model.number="eventHour" aria-label="时" min="0" max="23" @change="fixTime" /><span>:</span>
        <input type="number" v-model.number="eventMinute" aria-label="分" min="0" max="59" @change="fixTime" />
      </div>
          </fieldset>
          <label class="event-title-field"><input ref="titleInput" v-model="newEventTitle" aria-label="事件标题" placeholder="给事件起个标题…" maxlength="120" required /></label>
          <label class="event-content-field"><textarea v-model="newEventDesc" aria-label="事件描述" placeholder="写下这一刻发生的事…" maxlength="4000" required></textarea></label>
          <footer class="event-editor-actions">
            <button type="button" class="cancel-event" @click="$emit('cancel-record')">暂不记录</button>
            <button class="submit-event" :disabled="!newEventTitle.trim() || !newEventDesc.trim()" type="submit">保存事件<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4 4L19 6"/></svg></button>
          </footer>
        </form>
      </div>
    </Teleport>
    <p v-if="!sortedEvents.length" class="timeline-empty">从一个时间点，串起案件经过。</p>
    <div v-else class="timeline-scroll" tabindex="0" aria-label="选择时间节点，可同时展开多条事件">
      <div class="timeline-track">
        <section v-for="group in eventGroups" :key="group.date" class="date-group" :style="{ flexGrow: group.events.length }" :aria-label="group.date">
          <h3>{{ group.date }}</h3>
          <ol class="day-events">
            <li v-for="event in group.events" :key="event.id" class="timeline-event">
              <button class="event-summary" :aria-expanded="lockedEvents.has(event.id)" aria-controls="open-time-cards" :title="event.description" @click="toggleEvent(event)">
                <time>{{ clockTime(event.event_time) }}</time>
                <span class="event-excerpt">{{ event.title || '未命名事件' }}</span>
              </button>
            </li>
          </ol>
        </section>
      </div>
    </div>
    <Teleport to="body">
    <section v-if="active && openEvents.length" id="open-time-cards" class="time-cards" :style="{ top: overlayTop + 'px' }" aria-label="已展开事件，按时间排序" @click.self="$emit('close-all')" @keydown.esc="$emit('close-all')">
      <div class="cards-toolbar">
        <span>事件经过</span>
        <button @click="$emit('close-all')" aria-label="关闭所有时间卡片">全部关闭<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 6 12 12M6 18 18 6"/></svg></button>
      </div>
      <div class="cards-scroll" tabindex="0" aria-label="横向查看已展开的时间卡片" @click.self="$emit('close-all')">
        <ol class="cards-track">
          <li v-for="(event, index) in openEvents" :key="event.id" class="time-card-wrap">
            <svg v-if="index < openEvents.length - 1" class="connecting-thread" viewBox="0 0 284 70" aria-hidden="true">
              <path class="thread-shadow" :d="index % 2 ? 'M0 30 C90 65 194 -8 284 14' : 'M0 14 C90 -8 194 65 284 30'"/>
              <path :d="index % 2 ? 'M0 30 C90 65 194 -8 284 14' : 'M0 14 C90 -8 194 65 284 30'"/>
            </svg>
            <article class="time-card">
              <header><time>{{ event.event_time }}</time><button @click="$emit('close-popup', event)" :aria-label="'关闭时间卡片 ' + event.event_time" title="关闭这张卡片"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 6 12 12M6 18 18 6"/></svg></button></header>
              <h3>{{ event.title || '未命名事件' }}</h3>
              <p>{{ event.description }}</p>
              <footer><button @click="$emit('delete', event.id)" :aria-label="'删除事件 ' + event.event_time"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13M10 11v5m4-5v5"/></svg>删除事件</button></footer>
            </article>
          </li>
        </ol>
      </div>
    </section>
    </Teleport>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
const props = defineProps<{
  active: boolean
  showForm: boolean
  sortedEvents: any[]
  hoveredEvent: any
  lockedEvents: Set<number>
  eventYear: number
  eventMonth: number
  eventDay: number
  eventHour: number
  eventMinute: number
  newEventDesc: string
  newEventTitle: string
}>()

const emit = defineEmits<{
  'submit': []
  'cancel-record': []
  'delete': [eventId: number]
  'update:eventYear': [value: number]
  'update:eventMonth': [value: number]
  'update:eventDay': [value: number]
  'update:eventHour': [value: number]
  'update:eventMinute': [value: number]
  'update:newEventDesc': [value: string]
  'show-popup': [event: any]
  'dot-mouse-leave': [event: any]
  'popup-mouse-enter': [event: any]
  'popup-mouse-leave': [event: any]
  'lock-popup': [event: any]
  'close-popup': [event: any]
  'close-all': []
}>()

const eventYear = defineModel<number>('eventYear', { default: new Date().getFullYear() })
const eventMonth = defineModel<number>('eventMonth', { default: 1 })
const eventDay = defineModel<number>('eventDay', { default: 1 })
const eventHour = defineModel<number>('eventHour', { default: 0 })
const eventMinute = defineModel<number>('eventMinute', { default: 0 })
const newEventDesc = defineModel<string>('newEventDesc', { default: '' })
const newEventTitle = defineModel<string>('newEventTitle', { default: '' })

function fixDate() {
  if (eventMonth.value < 1) eventMonth.value = 1
  if (eventMonth.value > 12) eventMonth.value = 12
  const daysInMonth = new Date(eventYear.value, eventMonth.value, 0).getDate()
  if (eventDay.value < 1) eventDay.value = 1
  if (eventDay.value > daysInMonth) eventDay.value = daysInMonth
}

function fixTime() {
  if (eventHour.value < 0) eventHour.value = 0
  if (eventHour.value > 23) eventHour.value = 23
  if (eventMinute.value < 0) eventMinute.value = 0
  if (eventMinute.value > 59) eventMinute.value = 59
}

const openEvents = computed(() => props.sortedEvents.filter(event => props.lockedEvents.has(event.id)))
const editorForm = ref<HTMLFormElement | null>(null)
const titleInput = ref<HTMLInputElement | null>(null)
watch(() => props.showForm, async value => {
  await nextTick()
  if (value) titleInput.value?.focus()
  else document.querySelector<HTMLButtonElement>('.record-event-btn')?.focus()
})
function onEditorKeydown(event: KeyboardEvent) {
  if (event.isComposing) return
  if (event.key === 'Escape') {
    event.preventDefault()
    event.stopPropagation()
    emit('cancel-record')
  } else if ((event.ctrlKey || event.metaKey) && event.key === 'Enter' && !event.isComposing) {
    event.preventDefault()
    if (newEventTitle.value.trim() && newEventDesc.value.trim()) emit('submit')
  } else if (event.key === 'Enter' && event.target instanceof HTMLInputElement) {
    event.preventDefault()
    if (event.target.value.trim() && event.target.validity.valid) focusNextField(event.target)
  } else if (event.key === 'Tab') {
    const fields = editorForm.value?.querySelectorAll<HTMLElement>('button:not(:disabled), input, textarea')
    if (!fields?.length) return
    const first = fields[0], last = fields[fields.length - 1]
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus() }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus() }
  }
}
function focusNextField(current: HTMLInputElement) {
  const fields = Array.from(editorForm.value?.querySelectorAll<HTMLInputElement | HTMLTextAreaElement>('input, textarea') ?? [])
  const next = fields[fields.indexOf(current) + 1]
  next?.focus()
}
let enteredTimeDigits = 0
function selectTimeField(event: FocusEvent) {
  enteredTimeDigits = 0
  if (event.target instanceof HTMLInputElement) event.target.select()
}
function advanceTimeField(event: Event) {
  const input = event.target
  if (!(input instanceof HTMLInputElement)) return
  const inputEvent = event as InputEvent
  if (!inputEvent.inputType?.startsWith('insert') || inputEvent.isComposing) { enteredTimeDigits = 0; return }
  // Number models normalize 09 to 9; count typed digits before that normalization.
  enteredTimeDigits += /^\d+$/.test(inputEvent.data ?? '') ? inputEvent.data!.length : 0
  if (!input.validity.valid) return
  const digits = input.getAttribute('aria-label') === '年' ? 4 : 2
  if (/^\d+$/.test(input.value) && (input.value.length >= digits || enteredTimeDigits >= digits)) focusNextField(input)
}
const panelElement = ref<HTMLElement | null>(null)
const overlayTop = ref(137)
let panelObserver: ResizeObserver | undefined
function updateOverlayTop() {
  if (panelElement.value) overlayTop.value = Math.max(0, panelElement.value.getBoundingClientRect().bottom)
}
watch(() => [props.active, props.showForm, openEvents.value.length], async () => {
  await nextTick()
  updateOverlayTop()
})
onMounted(() => {
  panelObserver = new ResizeObserver(updateOverlayTop)
  if (panelElement.value) panelObserver.observe(panelElement.value)
  window.addEventListener('resize', updateOverlayTop)
  window.addEventListener('scroll', updateOverlayTop, true)
  // The parent reveal animates its transform independently of its size.
  panelElement.value?.closest('.timeline-reveal')?.addEventListener('transitionend', updateOverlayTop)
})
onBeforeUnmount(() => {
  panelObserver?.disconnect()
  window.removeEventListener('resize', updateOverlayTop)
  window.removeEventListener('scroll', updateOverlayTop, true)
  panelElement.value?.closest('.timeline-reveal')?.removeEventListener('transitionend', updateOverlayTop)
})

const eventGroups = computed(() => {
  const groups: { date: string; events: any[] }[] = []
  for (const event of props.sortedEvents) {
    const date = event.event_time.match(/^(\d+年\d+月\d+日)/)?.[1] || '未标注日期'
    const last = groups[groups.length - 1]
    if (last?.date === date) last.events.push(event)
    else groups.push({ date, events: [event] })
  }
  return groups
})
function clockTime(value: string) { return value.match(/(\d{1,2}:\d{2})/)?.[1] || value }
function toggleEvent(event: any) {
  if (props.lockedEvents.has(event.id)) emit('close-popup', event)
  else emit('lock-popup', event)
}

</script>

<style scoped>
.timeline-panel { position: relative; padding: 5px 26px 4px; background: #eae2ce; border-bottom: 1px solid #bdb095; box-sizing: border-box; color: #473f33; font-family: var(--serif); max-height: min(410px, 65vh); overflow-y: auto; scrollbar-width: thin; scrollbar-color: #b5a78b transparent; }
.datetime-picker { display: flex; gap: 2px; align-items: center; flex: none; }
.datetime-picker input { width: 34px; min-width: 0; padding: 6px 1px; border: 0; border-bottom: 1px solid #c1b69e; border-radius: 0; background: transparent; color: #64533f; text-align: center; font: 12px var(--mono); appearance: textfield; }
.datetime-picker input::-webkit-inner-spin-button, .datetime-picker input::-webkit-outer-spin-button { appearance: none; margin: 0; }
.datetime-picker input:first-child { width: 47px; }
.datetime-picker span { font-size: 11px; color: #998970; }
.submit-event { display: flex; align-items: center; gap: 5px; border: 0; border-radius: 2px; background: #d7d9bf; color: #4e624e; padding: 8px 12px; font: 13px var(--serif); cursor: pointer; }
.submit-event:disabled { opacity: .5; cursor: default; }
svg { width: 16px; height: 16px; fill: none; stroke: currentColor; stroke-width: 1.6; stroke-linecap: round; stroke-linejoin: round; }
.timeline-empty { margin: 0; padding: 18px 0; text-align: center; font-size: 12px; color: #8a7b63; }
.timeline-scroll { overflow-x: auto; scrollbar-width: thin; scrollbar-color: #b5a78b transparent; padding: 0 2px 3px; }
.timeline-track { display: flex; min-width: 100%; width: max-content; }
.date-group { flex-basis: 0; min-width: 0; }
.date-group h3 { margin: 0 0 2px; color: #978970; font: 10px/16px var(--serif); }
.day-events { position: relative; display: flex; list-style: none; padding: 0; margin: 0; }
.day-events::before { content: ''; position: absolute; left: 0; right: 0; top: 14px; border-top: 1px solid #b5a58a; }
.timeline-event { flex: 1 0 98px; min-width: 0; }
.event-summary { position: relative; display: flex; flex-direction: column; align-items: center; gap: 4px; width: 100%; border: 0; background: transparent; padding: 2px 8px 3px; cursor: pointer; color: #7a6852; }
.event-summary time { padding: 3px 7px; background: #eae2ce; border-radius: 2px; font: 12px/17px var(--mono); }
.event-summary[aria-expanded="true"] time { background: #98534a; color: #fff5e3; }
.event-summary:hover time { box-shadow: 0 0 0 1px #98534a55; }
.event-excerpt { width: 100%; max-width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #9a8d76; font: 11px/16px var(--serif); }
.time-cards { position: fixed; z-index: 1100; left: 0; right: 0; bottom: 0; display: flex; flex-direction: column; padding: 20px 28px 28px; background: rgba(31, 27, 21, .57); color: #473f33; font-family: var(--serif); }
.cards-toolbar { display: flex; flex: none; align-items: center; justify-content: space-between; color: #e2d5bc; font-size: 12px; }
.cards-toolbar button, .time-card button { display: inline-flex; align-items: center; gap: 5px; border: 0; background: transparent; color: #8b715b; cursor: pointer; font: 11px var(--serif); padding: 5px; }
.cards-toolbar button:hover, .time-card button:hover { color: #98534a; }
.cards-toolbar button { color: #f3e8d2; padding: 8px 10px; border: 1px solid #eadfc044; border-radius: 3px; }
.cards-toolbar button:hover { color: #fff8e9; background: #f3e8d214; }
.cards-scroll { display: flex; align-items: center; flex: 1; min-height: 0; overflow: auto; padding: 25px 12px 35px; scrollbar-width: thin; scrollbar-color: #b5a78b transparent; }
.cards-track { display: flex; flex: none; gap: 34px; width: max-content; list-style: none; margin: auto; padding: 0; align-items: flex-start; }
.time-card-wrap { position: relative; flex: 0 0 250px; width: 250px; padding-top: 10px; }
.time-card-wrap:nth-child(even) { padding-top: 26px; }
.time-card-wrap::before { content: ''; position: absolute; z-index: 3; left: 16px; top: 10px; width: 8px; height: 8px; border-radius: 50%; background: #99594c; box-shadow: inset 1px 1px 2px #e1a293, 1px 2px 2px #5d3d2a33; }
.time-card-wrap:nth-child(even)::before { top: 26px; }
.connecting-thread { position: absolute; z-index: 0; left: 20px; top: 0; width: 284px; height: 70px; overflow: visible; pointer-events: none; stroke: #a16c56; stroke-width: 1.6; }
.connecting-thread .thread-shadow { stroke: #755a3e28; stroke-width: 3; transform: translateY(2px); }
.time-card { position: relative; z-index: 1; padding: 14px 15px 9px; background: #faf2df; box-shadow: 1px 4px 8px #55402a20; transform: rotate(-.8deg); transform-origin: 20px 4px; }
.time-card-wrap:nth-child(even) .time-card { background: #f2eddd; transform: rotate(.8deg); }
.time-card header { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.time-card header time { font: 11px/1.5 var(--mono); color: #98534a; }
.time-card h3 { margin: 10px 0 0; color: #473f33; font: 18px/1.5 var(--serif); overflow-wrap: anywhere; }
.time-card p { font: 14px/1.8 var(--serif); margin: 11px 0 8px; white-space: pre-wrap; overflow-wrap: anywhere; max-height: min(260px, 30vh); overflow-y: auto; scrollbar-width: thin; scrollbar-color: #b5a78b transparent; }
.time-card footer { display: flex; justify-content: flex-end; }
button:focus-visible, .timeline-scroll:focus-visible, .cards-scroll:focus-visible { outline: 2px solid #8e9b74; outline-offset: 2px; }
.event-editor input:focus, .event-editor textarea:focus { outline: none; box-shadow: none; border-bottom-color: #98534a; }
@media (max-width: 600px) { .timeline-panel { padding: 5px 14px 4px; } }
@media (max-width: 600px) { .time-cards { padding: 12px 14px 18px; } .cards-scroll { padding-left: 6px; padding-right: 6px; } }
.event-editor-overlay { position: fixed; inset: 0; z-index: 1400; display: grid; place-items: center; padding: 24px; background: rgba(31,27,21,.57); color: #473f33; font-family: var(--serif); }
.event-editor { position: relative; width: min(520px, 100%); max-height: calc(100dvh - 48px); overflow-y: auto; padding: 38px 40px 25px; background: repeating-linear-gradient(transparent 0 31px, #9c8b6710 31px 32px), #f5edda; border-radius: 2px; box-shadow: 8px 16px 35px #231a1755; transform: rotate(-.35deg); scrollbar-width: thin; }
.event-editor::before { content: ''; position: absolute; top: 0; left: 30px; bottom: 0; border-left: 1px solid #b57c6940; pointer-events: none; }
.event-editor-close { position: absolute; right: 16px; top: 14px; display: grid; place-items: center; width: 32px; height: 32px; border: 0; border-radius: 50%; background: transparent; color: #82715b; cursor: pointer; }
.event-editor-heading { padding-bottom: 17px; margin-bottom: 22px; border-bottom: 1px solid #c9baa0; }
.event-editor-heading span { color: #948773; font-size: 11px; letter-spacing: .12em; }
.event-editor-heading h2 { margin: 7px 0 0; font: 28px/1.4 var(--serif); color: #403527; }
.event-date-field { border: 0; padding: 0; margin: 0 0 25px; }
.event-date-field legend { display: block; padding: 0; margin-bottom: 12px; font-size: 12px; color: #897860; }
.event-editor .datetime-picker { gap: 5px; flex-wrap: wrap; }
.event-editor .datetime-picker input { width: 37px; font-size: 14px; }
.event-editor .datetime-picker input:first-child { width: 57px; }
.event-content-field { display: block; }
.event-title-field { display: block; margin-bottom: 18px; }
.event-title-field input { width: 100%; padding: 7px 0; border: 0; border-bottom: 1px solid #c1b69e; border-radius: 0; color: #473f33; background: transparent; font: 18px/1.6 var(--serif); }
.event-title-field input::placeholder { color: #a19580; }
.event-content-field textarea { display: block; width: 100%; height: 155px; box-sizing: border-box; resize: none; padding: 7px 0; border: 0; border-bottom: 1px solid #c1b69e; border-radius: 0; background: transparent; color: #473f33; font: 16px/1.9 var(--serif); scrollbar-width: thin; scrollbar-color: #b5a78b transparent; }
.event-content-field textarea::placeholder { color: #a19580; }
.event-editor-actions { display: flex; justify-content: flex-end; align-items: center; gap: 20px; padding-top: 20px; }
.cancel-event { border: 0; background: transparent; color: #8b7b65; padding: 8px 0; font: 13px var(--serif); cursor: pointer; }
.event-editor .submit-event { padding: 9px 14px; font-size: 14px; }
@media (max-width: 600px) { .event-editor-overlay { padding: 18px; } .event-editor { padding: 30px 24px 20px; } .event-editor::before { left: 15px; } .event-editor .datetime-picker { gap: 2px; } }
@media (max-height: 700px) { .event-editor { padding-top: 25px; padding-bottom: 18px; } .event-editor-heading { padding-bottom: 12px; margin-bottom: 14px; } .event-date-field { margin-bottom: 15px; } .event-date-field legend, .event-content-field > span { margin-bottom: 8px; } .event-title-field { margin-bottom: 12px; } .event-content-field textarea { height: 95px; } .event-editor-actions { padding-top: 14px; } }
</style>
