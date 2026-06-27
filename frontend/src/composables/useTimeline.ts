import { ref, computed } from 'vue'
import {
  getTimelineEvents,
  createTimelineEvent,
  deleteTimelineEvent as deleteTimelineEventApi,
} from '@/api/index'

export function useTimeline(caseId: number) {
  const timelineOpen = ref(false)
  const showAddEvent = ref(false)
  const timelineEvents = ref<any[]>([])

  const eventYear = ref(new Date().getFullYear())
  const eventMonth = ref(1)
  const eventDay = ref(1)
  const eventHour = ref(0)
  const eventMinute = ref(0)
  const newEventDesc = ref('')

  const hoveredEvent = ref<any>(null)
  const lockedEvents = ref<Set<number>>(new Set())

  const sortedEvents = computed(() => {
    return [...timelineEvents.value].sort((a, b) => {
      return parseEventTime(a.event_time) - parseEventTime(b.event_time)
    })
  })

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
    if (match) {
      return `${match[2]}/${match[3]}`
    }
    return eventTime
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
      if (gap < minSpacing) {
        items[i].ideal = items[i - 1].ideal + minSpacing
      }
    }

    const maxIdeal = items[items.length - 1].ideal
    const scale = maxIdeal > 98 ? 98 / maxIdeal : 1

    const item = items.find(a => a.id === event.id)
    if (!item) return 50

    return Math.max(2, item.ideal * scale)
  }

  function parseEventTime(str: string): number {
    const match = str.match(/(\d+)年(\d+)月(\d+)日\s(\d+):(\d+)/)
    if (!match) return 0
    return new Date(+match[1], +match[2] - 1, +match[3], +match[4], +match[5]).getTime()
  }

  function showPopup(event: any) {
    if (!lockedEvents.value.has(event.id)) {
      hoveredEvent.value = event
    }
  }

  function onDotMouseLeave(event: any) {
    if (!lockedEvents.value.has(event.id)) {
      hoveredEvent.value = null
    }
  }

  function onPopupMouseEnter(event: any) {
    hoveredEvent.value = event
  }

  function onPopupMouseLeave(event: any) {
    if (!lockedEvents.value.has(event.id)) {
      hoveredEvent.value = null
    }
  }

  function lockPopup(event: any) {
    const newSet = new Set(lockedEvents.value)
    if (newSet.has(event.id)) {
      newSet.delete(event.id)
    } else {
      newSet.add(event.id)
    }
    lockedEvents.value = newSet
    hoveredEvent.value = event
  }

  function closePopup(event: any) {
    const newSet = new Set(lockedEvents.value)
    newSet.delete(event.id)
    lockedEvents.value = newSet
    hoveredEvent.value = null
  }

  function closeAllPopups() {
    lockedEvents.value = new Set()
    hoveredEvent.value = null
  }

  async function loadTimelineEvents() {
    try {
      const res = await getTimelineEvents(caseId)
      timelineEvents.value = res.data
    } catch (err) {
      console.error('加载时间线失败', err)
    }
  }

  async function addTimelineEvent() {
    if (!newEventDesc.value.trim()) return
    const eventTimeStr = `${eventYear.value}年${eventMonth.value}月${eventDay.value}日 ${String(eventHour.value).padStart(2, '0')}:${String(eventMinute.value).padStart(2, '0')}`

    try {
      await createTimelineEvent(caseId, {
        event_time: eventTimeStr,
        description: newEventDesc.value.trim(),
        source: 'manual',
      })
      newEventDesc.value = ''
      showAddEvent.value = false
      await loadTimelineEvents()
    } catch (err) {
      console.error('添加时间线事件失败', err)
    }
  }

  async function handleDeleteEvent(eventId: number) {
    try {
      await deleteTimelineEventApi(caseId, eventId)
      const newSet = new Set(lockedEvents.value)
      newSet.delete(eventId)
      lockedEvents.value = newSet
      hoveredEvent.value = null
      await loadTimelineEvents()
    } catch (err) {
      console.error('删除事件失败', err)
    }
  }

  return {
    timelineOpen,
    showAddEvent,
    timelineEvents,
    eventYear,
    eventMonth,
    eventDay,
    eventHour,
    eventMinute,
    newEventDesc,
    hoveredEvent,
    lockedEvents,
    sortedEvents,
    fixDate,
    fixTime,
    formatEventTime,
    getDotPosition,
    showPopup,
    onDotMouseLeave,
    onPopupMouseEnter,
    onPopupMouseLeave,
    lockPopup,
    closePopup,
    closeAllPopups,
    loadTimelineEvents,
    addTimelineEvent,
    handleDeleteEvent,
  }
}
