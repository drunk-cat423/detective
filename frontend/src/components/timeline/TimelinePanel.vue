<template>
  <section ref="panelElement" class="timeline-panel" aria-label="案件时间线">
    <form v-if="showForm" class="timeline-form" @submit.prevent="$emit('submit')">
      <div class="datetime-picker" aria-label="事件时间">
        <input type="number" v-model.number="eventYear" aria-label="年" min="1" @change="fixDate" /><span>年</span>
        <input type="number" v-model.number="eventMonth" aria-label="月" min="1" max="12" @change="fixDate" /><span>月</span>
        <input type="number" v-model.number="eventDay" aria-label="日" min="1" max="31" @change="fixDate" /><span>日</span>
        <input type="number" v-model.number="eventHour" aria-label="时" min="0" max="23" @change="fixTime" /><span>:</span>
        <input type="number" v-model.number="eventMinute" aria-label="分" min="0" max="59" @change="fixTime" />
      </div>
      <input class="event-description" v-model="newEventDesc" aria-label="事件描述" placeholder="那一刻，发生了什么…" @keydown.enter.prevent="submitEvent" />
      <button class="submit-event" :disabled="!newEventDesc.trim()" type="submit">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4 4L19 6"/></svg>记下
      </button>
    </form>
    <p v-if="!sortedEvents.length" class="timeline-empty">从一个时间点，串起案件经过。</p>
    <div v-else class="timeline-scroll" tabindex="0" aria-label="选择时间节点，可同时展开多条事件">
      <div class="timeline-track">
        <section v-for="group in eventGroups" :key="group.date" class="date-group" :style="{ flexGrow: group.events.length }" :aria-label="group.date">
          <h3>{{ group.date }}</h3>
          <ol class="day-events">
            <li v-for="event in group.events" :key="event.id" class="timeline-event">
              <button class="event-summary" :aria-expanded="lockedEvents.has(event.id)" aria-controls="open-time-cards" :title="event.description" @click="toggleEvent(event)">
                <time>{{ clockTime(event.event_time) }}</time>
                <span class="event-excerpt">{{ event.title || event.description }}</span>
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
}>()

const emit = defineEmits<{
  'submit': []
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
function submitEvent(event: KeyboardEvent) {
  if (event.isComposing) return
  if (newEventDesc.value.trim()) emit('submit')
}
</script>

<style scoped>
.timeline-panel { position: relative; padding: 5px 26px 4px; background: #eae2ce; border-bottom: 1px solid #bdb095; box-sizing: border-box; color: #473f33; font-family: var(--serif); max-height: min(410px, 65vh); overflow-y: auto; scrollbar-width: thin; scrollbar-color: #b5a78b transparent; }
.timeline-form { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; margin: 0 0 12px; padding: 3px 0 13px; border-bottom: 1px solid #c9bea8; }
.datetime-picker { display: flex; gap: 2px; align-items: center; flex: none; }
.datetime-picker input { width: 34px; min-width: 0; padding: 6px 1px; border: 0; border-bottom: 1px solid #c1b69e; border-radius: 0; background: transparent; color: #64533f; text-align: center; font: 12px var(--mono); appearance: textfield; }
.datetime-picker input::-webkit-inner-spin-button, .datetime-picker input::-webkit-outer-spin-button { appearance: none; margin: 0; }
.datetime-picker input:first-child { width: 47px; }
.datetime-picker span { font-size: 11px; color: #998970; }
.event-description { flex: 1; min-width: 150px; border: 0; border-bottom: 1px solid #c1b69e; border-radius: 0; padding: 7px 2px; font: 14px var(--serif); color: #473f33; background: transparent; }
.event-description::placeholder { color: #95866f; }
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
.time-card p { font: 14px/1.8 var(--serif); margin: 11px 0 8px; white-space: pre-wrap; overflow-wrap: anywhere; max-height: min(260px, 30vh); overflow-y: auto; scrollbar-width: thin; scrollbar-color: #b5a78b transparent; }
.time-card footer { display: flex; justify-content: flex-end; }
button:focus-visible, input:focus-visible, .timeline-scroll:focus-visible, .cards-scroll:focus-visible { outline: 2px solid #8e9b74; outline-offset: 2px; }
@media (max-width: 600px) { .timeline-panel { padding: 5px 14px 4px; } .timeline-form { gap: 9px; } .datetime-picker { width: 100%; } }
@media (max-width: 600px) { .time-cards { padding: 12px 14px 18px; } .cards-scroll { padding-left: 6px; padding-right: 6px; } }
</style>
