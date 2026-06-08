<template>
  <BaseEdge :path="path" :style="edgeStyle" />
  <EdgeLabelRenderer>
    <div
      :style="{
        position: 'absolute',
        transform: `translate(-50%, -50%) translate($(labelX)px, $(labelY)px)`,
        pointerEvents: 'all',
      }"
      class="custom-edge-label"
      @dblclick.stop="startEdit"
    >
      <template v-if="editing">
        <input
          ref="inputRef"
          v-model="editValue"
          @blur="save"
          @keyup.enter="save"
          @click.stop
          size="10"
        />
      </template>
      <template v-else>
        {{ label || '+ 添加备注' }}
      </template>
    </div>
  </EdgeLabelRenderer>
</template>

<script setup lang="ts">
import { BaseEdge, EdgeLabelRenderer, getBezierPath } from '@vue-flow/core'
import { ref, nextTick, computed } from 'vue'
import { inject } from 'vue';

const props = defineProps<{
  id: string
  sourceX: number
  sourceY: number
  targetX: number
  targetY: number
  sourcePosition: any
  targetPosition: any
  label?: string
}>()

const edgeStyle = { stroke: '#b1b1b7', strokeWidth: 2 }
const [path, labelX, labelY] = getBezierPath({
  sourceX: props.sourceX,
  sourceY: props.sourceY,
  sourcePosition: props.sourcePosition,
  targetX: props.targetX,
  targetY: props.targetY,
  targetPosition: props.targetPosition,
})

const editing = ref(false)
const editValue = ref(props.label || '')
const inputRef = ref<HTMLInputElement | null>(null)

const emit = defineEmits(['updateLabel'])

const updateEdgeLabel = inject('updateEdgeLabel') as (id: string, label: string) => void


function startEdit() {
  editing.value = true
  editValue.value = props.label || ''
  nextTick(() => {
    inputRef.value?.focus()
  })
}

function save() {
  const newLabel = editValue.value.trim()
  if (newLabel !== (props.label || '')) {
    emit('updateLabel', props.id, newLabel)
  }
  editing.value = false
}


</script>

<style scoped>
.custom-edge-label {
  background: white;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 12px;
  white-space: nowrap;
  cursor: pointer;
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}
.custom-edge-label:hover {
  background: #f0f0f0;
}
.custom-edge-label input {
  border: none;
  background: transparent;
  outline: none;
  font-size: 12px;
  width: auto;
  min-width: 80px;
}
</style>