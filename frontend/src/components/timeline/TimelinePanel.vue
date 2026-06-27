<template>
  <div class="timeline-panel">
    <!-- 添加表单 -->
    <div v-if="showForm" class="timeline-form">
      <div class="datetime-picker">
        <input type="number" v-model.number="eventYear" placeholder="年" min="1" @change="fixDate" />
        <span>-</span>
        <input type="number" v-model.number="eventMonth" placeholder="月" min="1" max="12" @change="fixDate" />
        <span>-</span>
        <input type="number" v-model.number="eventDay" placeholder="日" min="1" max="31" @change="fixDate" />
        <span>&nbsp;</span>
        <input type="number" v-model.number="eventHour" placeholder="时" min="0" max="23" @change="fixTime" />
        <span>:</span>
        <input type="number" v-model.number="eventMinute" placeholder="分" min="0" max="59" @change="fixTime" />
      </div>
      <input
        type="text"
        v-model="newEventDesc"
        placeholder="事件描述"
        @keyup.enter="$emit('submit')"
      />
      <button @click="$emit('submit')">添加</button>
    </div>

    <!-- 时间轴 -->
    <div class="timeline-axis" ref="timelineAxis" @click="closeAllPopups">
      <div class="axis-line"></div>

      <div
        v-for="event in sortedEvents"
        :key="event.id"
        class="timeline-dot-wrapper"
        :style="{ left: getDotPosition(event, sortedEvents) + '%' }"
      >
        <div
          class="timeline-dot"
          @mouseenter="showPopup(event)"
          @mouseleave="onDotMouseLeave(event)"
          @click.stop="lockPopup(event)"
        >
          <div class="dot"></div>
          <span class="dot-time">{{ formatEventTime(event.event_time) }}</span>
        </div>

        <div
          v-if="hoveredEvent?.id === event.id || lockedEvents.has(event.id)"
          class="event-popup"
          :class="{ 'popup-left': getDotPosition(event, sortedEvents) < 20, 'popup-right': getDotPosition(event, sortedEvents) > 80 }"
          @mouseenter="onPopupMouseEnter(event)"
          @mouseleave="onPopupMouseLeave(event)"
          @click.stop
        >
          <div class="popup-header">
            <strong>{{ event.event_time }}</strong>
            <button class="popup-close-btn" @click="closePopup(event)">✕</button>
          </div>
          <p>{{ event.description }}</p>
          <button class="popup-delete-btn" @click="$emit('delete', event.id)">删除事件</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
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

function formatEventTime(eventTime: string) {
  if (!eventTime) return ''
  const match = eventTime.match(/(\d+)年(\d+)月(\d+)日/)
  if (match) return `${match[2]}/${match[3]}`
  return eventTime
}

function parseEventTime(str: string): number {
  const match = str.match(/(\d+)年(\d+)月(\d+)日\s(\d+):(\d+)/)
  if (!match) return 0
  return new Date(+match[1], +match[2] - 1, +match[3], +match[4], +match[5]).getTime()
}

function getDotPosition(event: any, events: any[]) {
  if (events.length <= 1) return 50
  const sorted = [...events].sort((a, b) => parseEventTime(a.event_time) - parseEventTime(b.event_time))
  const firstTime = parseEventTime(sorted[0].event_time)
  const lastTime = parseEventTime(sorted[sorted.length - 1].event_time)
  const totalRange = lastTime - firstTime || 1

  const items = sorted.map(e => ({
    id: e.id,
    ideal: ((parseEventTime(e.event_time) - firstTime) / totalRange) * 100,
  }))

  const minSpacing = 5
  for (let i = 1; i < items.length; i++) {
    const gap = items[i].ideal - items[i - 1].ideal
    if (gap < minSpacing) items[i].ideal = items[i - 1].ideal + minSpacing
  }

  const maxIdeal = items[items.length - 1].ideal
  const scale = maxIdeal > 98 ? 98 / maxIdeal : 1
  const item = items.find(a => a.id === event.id)
  if (!item) return 50
  return Math.max(2, item.ideal * scale)
}

function showPopup(event: any) { emit('show-popup', event) }
function onDotMouseLeave(event: any) { emit('dot-mouse-leave', event) }
function onPopupMouseEnter(event: any) { emit('popup-mouse-enter', event) }
function onPopupMouseLeave(event: any) { emit('popup-mouse-leave', event) }
function lockPopup(event: any) { emit('lock-popup', event) }
function closePopup(event: any) { emit('close-popup', event) }
function closeAllPopups() { emit('close-all') }
</script>

<style scoped>
.timeline-panel {
  background: #F8F5EC;
  border-bottom: 1px solid #E0D5C0;
  padding: 12px 24px;
  position: relative;
  box-sizing: border-box;
}

.timeline-form {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 4px;
}

.datetime-picker {
  display: flex;
  gap: 2px;
  align-items: center;
  background: var(--white);
  padding: 4px 8px;
  border-radius: 8px;
  border: 1px solid #D4C9A8;
}

.datetime-picker input {
  width: 42px;
  padding: 3px 4px;
  border: none;
  border-radius: 4px;
  text-align: center;
  font-size: 12px;
  background: transparent;
  color: var(--text);
}

.datetime-picker input:first-child {
  width: 52px;
}

.datetime-picker input:focus {
  outline: none;
  background: var(--gold-pale);
}

.datetime-picker span {
  color: #B8A88A;
  font-weight: bold;
  font-size: 12px;
}

.timeline-form input[type="text"] {
  flex: 1;
  min-width: 160px;
  padding: 8px 14px;
  border: 1.5px solid #C4B99A;
  border-radius: 20px;
  font-size: 13px;
  background: #fff;
  outline: none;
  font-family: inherit;
  transition: border-color 0.2s;
}

.timeline-form input[type="text"]:focus {
  border-color: #D4A843;
}

.timeline-form button {
  padding: 8px 18px;
  background: #D4A843;
  border: 1.5px solid #B8922E;
  border-radius: 20px;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
  font-size: 12px;
  outline: none;
  transition: all 0.2s;
}

.timeline-form button:hover {
  background: #B8922E;
  border-color: #9A7A28;
  transform: translateY(-1px);
}

.timeline-axis {
  position: relative;
  height: 40px;
  margin: 8px 40px 0;
  display: flex;
  align-items: center;
}

.axis-line {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 2px;
  transform: translateY(-50%);
  background: linear-gradient(90deg, transparent, #D4C9A8, #C4B99A, #D4C9A8, transparent);
  border-radius: 1px;
}

.timeline-dot-wrapper {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  z-index: 2;
}

.timeline-dot {
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: transform 0.3s;
}

.timeline-dot:hover {
  transform: scale(1.15);
}

.dot {
  width: 14px;
  height: 14px;
  background: var(--white);
  border-radius: 50%;
  border: 2.5px solid #9A7A28;
  box-shadow: 0 0 0 3px rgba(212, 168, 67, 0.2);
  transition: all 0.3s;
}

.timeline-dot:hover .dot {
  border-color: #D4A843;
  box-shadow: 0 0 0 5px rgba(212, 168, 67, 0.25);
  transform: scale(1.1);
}

.dot-time {
  position: absolute;
  top: 22px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 10px;
  color: #8B7D6B;
  font-weight: 600;
  white-space: nowrap;
  background: var(--white);
  padding: 2px 6px;
  border-radius: 6px;
  border: 1px solid #E0D5C0;
}

.event-popup {
  position: absolute;
  top: 30px;
  left: 50%;
  transform: translateX(-50%);
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 8px 12px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.18);
  width: 200px;
  z-index: 30;
  pointer-events: auto;
}

.popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.popup-header strong {
  font-size: 12px;
  color: #333;
}

.popup-close-btn {
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  font-size: 14px;
  padding: 0;
  line-height: 1;
}

.popup-close-btn:hover {
  color: #333;
}

.event-popup p {
  margin: 4px 0;
  font-size: 12px;
  color: #555;
}

.popup-delete-btn {
  margin-top: 4px;
  padding: 2px 10px;
  background: #ffebee;
  border: 1px solid #e0c0c0;
  border-radius: 4px;
  color: #c62828;
  cursor: pointer;
  font-size: 12px;
}

.popup-delete-btn:hover {
  background: #ffcdd2;
}

.event-popup.popup-left {
  left: 0;
  transform: translateX(0);
}

.event-popup.popup-right {
  left: auto;
  right: 0;
  transform: translateX(0);
}
</style>
