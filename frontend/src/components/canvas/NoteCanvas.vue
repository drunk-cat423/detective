<template>
  <div
    ref="viewportRef"
    class="canvas-area"
    :class="{ placing: placingType, panning: panState }"
    :style="canvasStyle"
    @pointerdown="beginPan"
    @click="handlePaneClick"
    @wheel.prevent="handleWheel"
  >
    <div class="canvas-heading" @pointerdown.stop>
      <div>
        <span class="eyebrow">CASE EVIDENCE / 调查墙</span>
        <strong>{{ nodes.length }} 份档案 · {{ edges.length }} 条关联</strong>
      </div>
      <label class="search-box">
        <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6"/><path d="m16 16 4 4"/></svg>
        <input ref="searchInput" v-model="searchQuery" placeholder="搜索线索或嫌疑人" aria-label="搜索线索或嫌疑人" />
        <kbd>Ctrl K</kbd>
      </label>
    </div>

    <div class="board-world" :style="worldStyle">
      <svg class="edge-layer" overflow="visible" aria-label="线索关联">
        <ThreadEdge
          v-for="item in edgeModels"
          :key="item.edge.id"
          :source-x="item.source.x"
          :source-y="item.source.y"
          :target-x="item.target.x"
          :target-y="item.target.y"
          :label="item.edge.label"
          @edge-dblclick="event => onEdgeDoubleClick(item.edge, event)"
        />
      </svg>

      <div
        v-for="node in nodes"
        :key="node.id"
        class="board-card"
        :style="nodePositionStyle(node)"
        @pointerdown.stop="beginCardDrag(node, $event)"
        @click.stop="handleCardClick(node)"
        @dblclick.stop="handleCardDoubleClick(node, $event)"
      >
        <NoteNode :id="String(node.id)" :data="node.data" />
      </div>
    </div>

    <Transition name="placement">
      <div v-if="placingType || linkingSourceId" class="placement-hint" :class="{ linking: linkingSourceId }" @pointerdown.stop>
        <span class="placement-dot"></span>
        <template v-if="linkingSourceId">再点击一张卡片，图钉之间将拉出线绳</template>
        <template v-else>点击调查墙，固定{{ placingType === 'clue' ? '线索' : '嫌疑人档案' }}</template>
        <button @click="cancelActiveMode">取消</button>
      </div>
    </Transition>

    <div
      v-if="editingEdgeForLabel"
      class="edge-edit-toolbar"
      :style="{ left: editEdgePosition.x + 'px', top: editEdgePosition.y + 'px' }"
      @click.stop
      @pointerdown.stop
    >
      <div class="edge-edit-input-wrapper">
        <input
          :value="editEdgeLabelText"
          type="text"
          placeholder="输入备注..."
          autofocus
          @keyup.enter="saveEdgeLabelEdit"
          @blur="saveEdgeLabelEdit"
          @input="emit('update:editEdgeLabelText', ($event.target as HTMLInputElement).value)"
        />
      </div>
      <button class="edge-delete-btn" @mousedown.stop.prevent="deleteCurrentEdge" title="删除连线">🗑️</button>
    </div>

    <button class="center-btn" @pointerdown.stop @click.stop="goToCenter" title="回到调查墙中心" aria-label="回到调查墙中心">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 8V4h4M16 4h4v4M20 16v4h-4M8 20H4v-4"/><circle cx="12" cy="12" r="2.5"/></svg>
    </button>

    <div class="add-note-bar" @pointerdown.stop>
      <span>固定新档案</span>
      <button class="clue-btn" @click.stop="startPlacement('clue')"><b>＋</b> 线索</button>
      <button class="suspect-btn" @click.stop="startPlacement('suspect')"><b>＋</b> 嫌疑人</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, provide, ref, toRef, watch, type CSSProperties } from 'vue'
import NoteNode from '@/components/NoteNode.vue'
import ThreadEdge from '@/components/canvas/ThreadEdge.vue'
import { nodePinAnchor, nodeSize } from '@/utils/boardGeometry'
import { createLinenTexture } from '@/utils/linenTexture'

const props = defineProps<{
  nodes: any[]
  edges: any[]
  editingEdgeForLabel: any
  editEdgeLabelText: string
  editEdgePosition: { x: number; y: number }
  defaultEdgeOptions?: any
  selectedNodeId?: string
}>()

const emit = defineEmits<{
  'update:nodes': [nodes: any[]]
  'update:edges': [edges: any[]]
  'update:editEdgeLabelText': [value: string]
  'select-node': [node: any]
  'open-node-editor': [payload: { node: any; rect: { left: number; top: number; width: number; height: number } }]
  'deselect-node': []
  'go-to-center': [controller: any]
  'on-connect': [connection: any]
  'on-nodes-change': [changes: any[]]
  'on-edge-double-click': [params: any]
  'save-edge-label-edit': []
  'delete-current-edge': []
  'add-note': [payload: { type: string; position: { x: number; y: number } }]
  'delete-node': [node: any]
}>()

const viewportRef = ref<HTMLElement | null>(null)
const searchInput = ref<HTMLInputElement | null>(null)
const searchQuery = ref('')
const placingType = ref<'clue' | 'suspect' | null>(null)
const menuNodeId = ref<string | null>(null)
const linkingSourceId = ref<string | null>(null)
const camera = ref({ x: 80, y: 70, zoom: 1 })
const panState = ref<null | { startX: number; startY: number; cameraX: number; cameraY: number; moved: boolean }>(null)
const dragState = ref<null | { id: string; startX: number; startY: number; nodeX: number; nodeY: number; moved: boolean }>(null)
const suppressClickId = ref<string | null>(null)
const linenTexture = ref('')
let initialFitComplete = false

provide('noteSearchQuery', searchQuery)
provide('selectedNodeId', toRef(props, 'selectedNodeId'))
provide('menuNodeId', menuNodeId)
provide('linkingSourceId', linkingSourceId)
provide('linkedPins', computed(() => {
  const pins = new Set<string>()
  props.edges.forEach(edge => {
    pins.add(String(edge.source))
    pins.add(String(edge.target))
  })
  return pins
}))
provide('runNodeAction', runNodeAction)

const nodes = computed(() => props.nodes)
const edges = computed(() => props.edges)
const worldStyle = computed<CSSProperties>(() => ({
  transform: `translate3d(${camera.value.x}px, ${camera.value.y}px, 0) scale(${camera.value.zoom})`,
}))
const canvasStyle = computed<CSSProperties>(() => ({
  '--linen-image': linenTexture.value ? `url("${linenTexture.value}")` : 'none',
}))

const edgeModels = computed(() => props.edges.flatMap(edge => {
  const sourceNode = props.nodes.find(node => String(node.id) === String(edge.source))
  const targetNode = props.nodes.find(node => String(node.id) === String(edge.target))
  if (!sourceNode || !targetNode) return []
  return [{ edge, source: nodePinAnchor(sourceNode), target: nodePinAnchor(targetNode) }]
}))

function fitView() {
  const viewport = viewportRef.value
  if (!viewport || !props.nodes.length) return
  const bounds = props.nodes.reduce((acc, node) => {
    const { width, height } = nodeSize(node)
    const x = Number(node.position?.x ?? 0)
    const y = Number(node.position?.y ?? 0)
    return {
      minX: Math.min(acc.minX, x),
      minY: Math.min(acc.minY, y),
      maxX: Math.max(acc.maxX, x + width),
      maxY: Math.max(acc.maxY, y + height),
    }
  }, { minX: Infinity, minY: Infinity, maxX: -Infinity, maxY: -Infinity })
  const boardWidth = Math.max(1, bounds.maxX - bounds.minX)
  const boardHeight = Math.max(1, bounds.maxY - bounds.minY)
  const controlRail = Math.min(68, viewport.clientWidth * .18)
  const usableWidth = viewport.clientWidth - controlRail
  const paddingX = Math.min(150, usableWidth * .14)
  const paddingY = Math.min(130, viewport.clientHeight * .18)
  const zoom = Math.min(1.15, Math.max(.16,
    Math.min(
      (usableWidth - paddingX * 2) / boardWidth,
      (viewport.clientHeight - paddingY * 2) / boardHeight,
    ),
  ))
  const centerX = (bounds.minX + bounds.maxX) / 2
  const centerY = (bounds.minY + bounds.maxY) / 2
  camera.value = {
    zoom,
    x: usableWidth / 2 - centerX * zoom,
    y: viewport.clientHeight / 2 - centerY * zoom,
  }
}

function nodePositionStyle(node: any): CSSProperties {
  const { width, height } = nodeSize(node)
  return {
    width: `${width}px`,
    height: `${height}px`,
    transform: `translate3d(${Number(node.position?.x ?? 0)}px, ${Number(node.position?.y ?? 0)}px, 0)`,
  }
}

function screenToWorld(clientX: number, clientY: number) {
  const rect = viewportRef.value?.getBoundingClientRect()
  if (!rect) return { x: clientX, y: clientY }
  return {
    x: (clientX - rect.left - camera.value.x) / camera.value.zoom,
    y: (clientY - rect.top - camera.value.y) / camera.value.zoom,
  }
}

function beginPan(event: PointerEvent) {
  if (event.button !== 0 || placingType.value) return
  const target = event.target as HTMLElement
  if (target.closest('.canvas-heading,.add-note-bar,.center-btn,.placement-hint,.edge-edit-toolbar,.thread-hitbox')) return
  panState.value = {
    startX: event.clientX,
    startY: event.clientY,
    cameraX: camera.value.x,
    cameraY: camera.value.y,
    moved: false,
  }
}

function beginCardDrag(node: any, event: PointerEvent) {
  if (event.button !== 0 || linkingSourceId.value || placingType.value) return
  event.preventDefault()
  dragState.value = {
    id: String(node.id),
    startX: event.clientX,
    startY: event.clientY,
    nodeX: Number(node.position?.x ?? 0),
    nodeY: Number(node.position?.y ?? 0),
    moved: false,
  }
}

function onPointerMove(event: PointerEvent) {
  if (dragState.value) {
    const dx = (event.clientX - dragState.value.startX) / camera.value.zoom
    const dy = (event.clientY - dragState.value.startY) / camera.value.zoom
    if (Math.hypot(dx, dy) > 2) dragState.value.moved = true
    const position = { x: dragState.value.nodeX + dx, y: dragState.value.nodeY + dy }
    emit('update:nodes', props.nodes.map(node => String(node.id) === dragState.value?.id ? { ...node, position } : node))
    return
  }
  if (panState.value) {
    const dx = event.clientX - panState.value.startX
    const dy = event.clientY - panState.value.startY
    if (Math.hypot(dx, dy) > 2) panState.value.moved = true
    camera.value = { ...camera.value, x: panState.value.cameraX + dx, y: panState.value.cameraY + dy }
  }
}

function onPointerUp() {
  if (dragState.value) {
    const finished = dragState.value
    const node = props.nodes.find(item => String(item.id) === finished.id)
    if (finished.moved && node) {
      suppressClickId.value = finished.id
      emit('on-nodes-change', [{ type: 'position', id: finished.id, position: { ...node.position } }])
    }
    dragState.value = null
  }
  if (panState.value) {
    if (panState.value.moved) suppressClickId.value = '__pane__'
    panState.value = null
  }
}

function handleWheel(event: WheelEvent) {
  const rect = viewportRef.value?.getBoundingClientRect()
  if (!rect) return
  const oldZoom = camera.value.zoom
  const nextZoom = Math.min(2.2, Math.max(.45, oldZoom * Math.exp(-event.deltaY * .0012)))
  const localX = event.clientX - rect.left
  const localY = event.clientY - rect.top
  const worldX = (localX - camera.value.x) / oldZoom
  const worldY = (localY - camera.value.y) / oldZoom
  camera.value = {
    zoom: nextZoom,
    x: localX - worldX * nextZoom,
    y: localY - worldY * nextZoom,
  }
}

function handleCardClick(node: any) {
  if (suppressClickId.value === String(node.id)) {
    suppressClickId.value = null
    return
  }
  if (linkingSourceId.value) {
    if (linkingSourceId.value === String(node.id)) {
      linkingSourceId.value = null
      return
    }
    emit('on-connect', {
      source: linkingSourceId.value,
      target: String(node.id),
      sourceHandle: 'thread-source-pin',
      targetHandle: 'thread-target-pin',
    })
    linkingSourceId.value = null
    menuNodeId.value = null
    return
  }
  menuNodeId.value = null
}

function handleCardDoubleClick(node: any, event: MouseEvent) {
  if (linkingSourceId.value || placingType.value || suppressClickId.value === String(node.id)) return
  menuNodeId.value = null
  emit('select-node', node)
  const rect = (event.currentTarget as HTMLElement).getBoundingClientRect()
  emit('open-node-editor', {
    node,
    rect: { left: rect.left, top: rect.top, width: rect.width, height: rect.height },
  })
}

function handlePaneClick(event: MouseEvent) {
  if (suppressClickId.value === '__pane__') {
    suppressClickId.value = null
    return
  }
  const target = event.target as HTMLElement
  if (target.closest('.board-card,.thread-hitbox,.canvas-heading,.add-note-bar,.center-btn,.placement-hint,.edge-edit-toolbar')) return
  if (!placingType.value) {
    emit('deselect-node')
    menuNodeId.value = null
    linkingSourceId.value = null
    return
  }
  emit('add-note', { type: placingType.value, position: screenToWorld(event.clientX, event.clientY) })
  placingType.value = null
}

function runNodeAction(action: 'link', nodeId: string) {
  const node = props.nodes.find(item => String(item.id) === String(nodeId))
  if (!node) return
  if (action === 'link') {
    menuNodeId.value = null
    linkingSourceId.value = String(node.id)
  }
}

function onEdgeDoubleClick(edge: any, event: MouseEvent) {
  emit('on-edge-double-click', { edge, event })
}

function goToCenter() { fitView() }
function saveEdgeLabelEdit() { emit('save-edge-label-edit') }
function deleteCurrentEdge() { emit('delete-current-edge') }
function startPlacement(type: 'clue' | 'suspect') { placingType.value = type }
function cancelActiveMode() {
  placingType.value = null
  linkingSourceId.value = null
  menuNodeId.value = null
}

function onShortcut(event: KeyboardEvent) {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
    event.preventDefault()
    searchInput.value?.focus()
  }
  if (event.key === 'Escape') cancelActiveMode()
}

onMounted(() => {
  linenTexture.value = createLinenTexture()
  window.addEventListener('pointermove', onPointerMove)
  window.addEventListener('pointerup', onPointerUp)
  window.addEventListener('keydown', onShortcut)
})

watch(() => props.nodes.length, async length => {
  if (!length || initialFitComplete) return
  initialFitComplete = true
  await nextTick()
  requestAnimationFrame(fitView)
}, { immediate: true })

onBeforeUnmount(() => {
  window.removeEventListener('pointermove', onPointerMove)
  window.removeEventListener('pointerup', onPointerUp)
  window.removeEventListener('keydown', onShortcut)
})
</script>

<style scoped>
.canvas-area {
  flex: 1;
  position: relative;
  min-width: 0;
  overflow: hidden;
  touch-action: none;
  cursor: grab;
  border: 8px solid #846d53;
  border-left-width: 7px;
  border-radius: 3px 15px 15px 3px;
  box-shadow:
    inset 0 0 0 1px rgba(255,244,223,.42),
    inset 0 0 58px rgba(77,55,34,.12),
    0 18px 46px rgba(62,43,25,.16);
  background-color: #d7c4a4;
  background-image:
    linear-gradient(132deg, rgba(255,250,237,.13), transparent 46%, rgba(88,61,34,.055)),
    var(--linen-image);
  background-position: center;
  background-size: cover;
  background-repeat: no-repeat;
  isolation: isolate;
}
.canvas-area.panning { cursor: grabbing; }
.canvas-area.placing { cursor: crosshair; }
.canvas-area::before,.canvas-area::after { content:''; position:absolute; inset:0; z-index:0; pointer-events:none; }
.canvas-area::before {
  background:
    radial-gradient(ellipse at 24% 18%, rgba(255,250,237,.1), transparent 31%),
    radial-gradient(ellipse at 76% 72%, rgba(91,62,35,.065), transparent 42%);
  box-shadow: inset 0 0 74px rgba(75,52,31,.09);
}
.canvas-area::after {
  opacity:.44;
  background: linear-gradient(90deg, rgba(255,255,255,.045), transparent 22%, transparent 78%, rgba(73,49,28,.05));
  mix-blend-mode:soft-light;
}
.board-world { position:absolute; z-index:1; top:0; left:0; width:1px; height:1px; transform-origin:0 0; will-change:transform; }
.edge-layer { position:absolute; z-index:1; top:0; left:0; width:1px; height:1px; pointer-events:auto; overflow:visible; }
.board-card { position:absolute; z-index:2; top:0; left:0; cursor:grab; will-change:transform; }
.board-card:active { cursor:grabbing; }

.canvas-heading { position:absolute; z-index:12; top:24px; left:28px; right:28px; display:flex; justify-content:space-between; align-items:flex-start; pointer-events:none; }
.canvas-heading>* { pointer-events:auto; }
.canvas-heading>div { display:flex; flex-direction:column; gap:5px; color:rgba(76,49,28,.64); text-shadow:0 1px rgba(255,245,226,.48); }
.canvas-heading strong { font-family:var(--serif); font-size:22px; font-weight:600; color:#50341f; }
.eyebrow { font-family:var(--mono); font-size:9px; letter-spacing:.18em; }
.search-box { width:min(300px,34vw); height:40px; display:flex; align-items:center; gap:9px; padding:0 12px; border:1px solid rgba(73,58,41,.18); border-radius:999px; background:rgba(247,243,234,.92); box-shadow:0 6px 20px rgba(57,44,28,.09); }
.search-box svg { width:16px; fill:none; stroke:var(--ink-faint); stroke-width:1.8; }
.search-box input { flex:1; min-width:0; border:0; outline:0; color:var(--ink); background:transparent; font-size:12px; }
.search-box kbd { color:var(--ink-faint); font:9px var(--mono); padding:3px 5px; border-radius:4px; background:rgba(93,76,54,.08); }

.placement-hint { position:absolute; z-index:20; left:50%; bottom:98px; transform:translateX(-50%); display:flex; align-items:center; gap:9px; padding:10px 12px 10px 15px; color:#f8f1e6; background:rgba(41,36,30,.94); border-radius:999px; box-shadow:0 14px 30px rgba(39,30,21,.3); font-size:12px; }
.placement-dot { width:7px; height:7px; border-radius:50%; background:#e9a67d; box-shadow:0 0 0 5px rgba(233,166,125,.12); }
.placement-hint button { border:0; color:#e8b69a; background:transparent; cursor:pointer; }
.placement-enter-active,.placement-leave-active { transition:opacity .18s ease-out,transform .2s cubic-bezier(.23,1,.32,1); }
.placement-enter-from,.placement-leave-to { opacity:0; transform:translate(-50%,10px); }

.add-note-bar { position:absolute; bottom:24px; left:28px; z-index:10; display:flex; gap:8px; align-items:center; padding:7px; border:1px solid rgba(79,61,42,.15); border-radius:999px; background:rgba(247,243,234,.94); box-shadow:0 10px 28px rgba(57,44,28,.14); }
.add-note-bar>span { padding:0 8px; color:var(--ink-faint); font:9px var(--mono); letter-spacing:.12em; }
.add-note-bar button { padding:9px 14px; border:0; border-radius:999px; color:var(--ink); font-weight:600; cursor:pointer; font-size:13px; background:#f0dfbd; transition:transform .16s ease-out,box-shadow .2s ease; }
.add-note-bar .suspect-btn { background:#dfc3bd; }
.add-note-bar button b { font-size:17px; font-weight:400; vertical-align:-1px; }
.add-note-bar button:hover { transform:translateY(-2px); box-shadow:0 7px 16px rgba(60,45,29,.14); }
.add-note-bar button:active { transform:scale(.97); }

.center-btn { position:absolute; bottom:24px; right:24px; z-index:10; width:44px; height:44px; border-radius:50%; border:1px solid rgba(79,61,42,.18); background:rgba(247,243,234,.94); display:flex; align-items:center; justify-content:center; cursor:pointer; box-shadow:var(--shadow); transition:transform .16s ease-out,background .2s ease; line-height:0; padding:0; }
.center-btn:hover { background:var(--white); transform:scale(1.06); }
.center-btn:active { transform:scale(.96); }
.center-btn svg { width:20px; height:20px; fill:none; stroke:var(--ink-soft); stroke-width:1.7; }

.edge-edit-toolbar { position:fixed; transform:translate(-50%,-50%); z-index:1000; display:flex; gap:10px; align-items:center; }
.edge-edit-input-wrapper { background:rgba(255,253,248,.96); border-radius:24px; box-shadow:0 2px 8px rgba(0,0,0,.1); border:1px solid var(--rust); padding:4px 12px; }
.edge-edit-input-wrapper input { border:0; background:transparent; outline:0; font-size:16px; padding:6px 0; min-width:120px; text-align:center; color:var(--text); }
.edge-delete-btn { background:white; border:1px solid #ddd; border-radius:50%; width:34px; height:34px; cursor:pointer; display:flex; align-items:center; justify-content:center; box-shadow:0 2px 6px rgba(0,0,0,.1); padding:0; }
.edge-delete-btn:hover { background:#ffebee; border-color:#c62828; color:#c62828; }

@media (max-width:760px) {
  .canvas-heading { left:16px; right:16px; }
  .canvas-heading>div { display:none; }
  .search-box { margin-left:auto; width:min(260px,76vw); }
  .search-box kbd,.add-note-bar>span { display:none; }
  .add-note-bar { left:14px; bottom:14px; }
  .center-btn { right:14px; bottom:14px; }
}

@media (prefers-reduced-motion:reduce) {
  .board-world,.board-card { will-change:auto; }
}
</style>
