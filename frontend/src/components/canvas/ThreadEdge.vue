<template>
  <g class="thread-edge">
    <path :d="edgePath" class="thread-shadow" />
    <path :d="edgePath" class="thread-strand" />
    <path :d="edgePath" class="thread-glint" />
    <path :d="edgePath" class="thread-hitbox" @dblclick.stop="emit('edge-dblclick', $event)" />
    <g v-if="label" class="thread-label" :transform="`translate(${geometry.labelX} ${geometry.labelY})`">
      <rect :x="-labelWidth / 2" y="-11" :width="labelWidth" height="22" rx="2" />
      <text text-anchor="middle" dominant-baseline="central">{{ label }}</text>
    </g>
  </g>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  sourceX: number
  sourceY: number
  targetX: number
  targetY: number
  label?: string
}>()

const emit = defineEmits<{ 'edge-dblclick': [event: MouseEvent] }>()

const geometry = computed(() => {
  const dx = props.targetX - props.sourceX
  const dy = props.targetY - props.sourceY
  const distance = Math.hypot(dx, dy)
  const sag = Math.min(88, Math.max(22, distance * .12))
  return {
    path: `M ${props.sourceX} ${props.sourceY} C ${props.sourceX + dx * .28} ${props.sourceY + dy * .28 + sag}, ${props.targetX - dx * .28} ${props.targetY - dy * .28 + sag}, ${props.targetX} ${props.targetY}`,
    labelX: (props.sourceX + props.targetX) / 2,
    labelY: (props.sourceY + props.targetY) / 2 + sag * .72,
  }
})

const edgePath = computed(() => geometry.value.path)
const labelWidth = computed(() => Math.min(180, Math.max(52, String(props.label ?? '').length * 13 + 18)))
</script>

<style scoped>
.thread-shadow,
.thread-strand,
.thread-glint,
.thread-hitbox { fill: none; stroke-linecap: round; stroke-linejoin: round; }
.thread-shadow { stroke: rgba(34,17,12,.42); stroke-width: 4.6px; transform: translate(2px,4px); filter: blur(1px); }
.thread-strand { stroke: #8f302b; stroke-width: 2.8px; filter: drop-shadow(0 1px 0 rgba(255,227,206,.14)); }
.thread-glint { stroke: rgba(231,129,107,.54); stroke-width: .65px; transform: translate(-.45px,-.45px); }
.thread-hitbox { stroke: transparent; stroke-width: 20px; pointer-events: stroke; cursor: pointer; }
.thread-edge:hover .thread-strand { stroke: #a53c34; stroke-width: 3.4px; }
.thread-label { pointer-events: none; }
.thread-label rect { fill: #e9ddc4; stroke: rgba(71,49,29,.2); filter: drop-shadow(2px 3px 4px rgba(32,20,12,.18)); }
.thread-label text { fill: #3e3328; font: 10px var(--serif); }
</style>
