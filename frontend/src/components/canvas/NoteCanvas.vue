<template>
  <div
    ref="viewportRef"
    class="canvas-area"
    :class="{ placing: placingType, panning: panState, 'panel-open': panelOpen }"
    :style="canvasStyle"
    @pointerdown="beginPan"
    @click="handlePaneClick"
    @wheel.prevent="handleWheel"
  >
    <div class="canvas-heading" @pointerdown.stop>
      <button class="center-btn" :tabindex="panelOpen ? -1 : 0" :aria-hidden="panelOpen" @click.stop="goToCenter" title="回到调查墙中心" aria-label="回到调查墙中心">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 8V4h4M16 4h4v4M20 16v4h-4M8 20H4v-4"/><circle cx="12" cy="12" r="2.5"/></svg>
      </button>
    </div>

    <div ref="worldRef" class="board-world" :class="{ centering: isCentering }" :style="worldStyle">
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

    <div class="add-note-dock" :class="{ open: addMenuOpen }" @pointerdown.stop>
      <div id="new-material-menu" class="material-cards" :aria-hidden="!addMenuOpen">
        <button class="material-card clue-card" :tabindex="addMenuOpen ? 0 : -1" @click.stop="startPlacement('clue')">
          <span class="material-code">E-01</span>
          <strong>线索</strong>
          <small>证物便签</small>
        </button>
        <button class="material-card suspect-card" :tabindex="addMenuOpen ? 0 : -1" @click.stop="startPlacement('suspect')">
          <span class="material-code">P-02</span>
          <strong>嫌疑人</strong>
          <small>人物档案</small>
        </button>
      </div>
      <button
        class="add-note-trigger"
        type="button"
        aria-controls="new-material-menu"
        :aria-expanded="addMenuOpen"
        @click.stop="toggleMaterialMenu"
      >
        <span class="card-stack" aria-hidden="true"></span>
        <span class="brass-fastener" aria-hidden="true"></span>
        <span class="trigger-copy"><small>NEW FILE</small><strong>登记材料</strong></span>
        <span class="trigger-plus" aria-hidden="true">＋</span>
      </button>
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
  searchQuery: string
  panelOpen: boolean
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
const worldRef = ref<HTMLElement | null>(null)
const isCentering = ref(false)
let centerAnimationTimer: ReturnType<typeof setTimeout> | undefined
const addMenuOpen = ref(false)
const placingType = ref<'clue' | 'suspect' | null>(null)
const menuNodeId = ref<string | null>(null)
const linkingSourceId = ref<string | null>(null)
const camera = ref({ x: 80, y: 70, zoom: 1 })
const panState = ref<null | { startX: number; startY: number; cameraX: number; cameraY: number; moved: boolean }>(null)
const dragState = ref<null | { id: string; startX: number; startY: number; nodeX: number; nodeY: number; moved: boolean }>(null)
const suppressClickId = ref<string | null>(null)
const linenTexture = ref('')
let initialFitComplete = false

provide('noteSearchQuery', toRef(props, 'searchQuery'))
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
  if (target.closest('.canvas-heading,.add-note-dock,.center-btn,.placement-hint,.edge-edit-toolbar,.thread-hitbox')) return
  stopCentering()
  addMenuOpen.value = false
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
  stopCentering()
  addMenuOpen.value = false
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
  stopCentering()
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
  if (target.closest('.board-card,.thread-hitbox,.canvas-heading,.add-note-dock,.center-btn,.placement-hint,.edge-edit-toolbar')) return
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

function stopCentering() {
  if (!isCentering.value) return
  const world = worldRef.value
  if (world) {
    const transform = new DOMMatrixReadOnly(getComputedStyle(world).transform)
    camera.value = { x: transform.m41, y: transform.m42, zoom: transform.m11 }
  }
  isCentering.value = false
  clearTimeout(centerAnimationTimer)
}

async function goToCenter() {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    fitView()
    return
  }
  stopCentering()
  isCentering.value = true
  await nextTick()
  requestAnimationFrame(() => {
    fitView()
    clearTimeout(centerAnimationTimer)
    centerAnimationTimer = setTimeout(() => { isCentering.value = false }, 440)
  })
}
function saveEdgeLabelEdit() { emit('save-edge-label-edit') }
function deleteCurrentEdge() { emit('delete-current-edge') }
function toggleMaterialMenu() {
  addMenuOpen.value = !addMenuOpen.value
}
function startPlacement(type: 'clue' | 'suspect') {
  addMenuOpen.value = false
  placingType.value = type
}
function cancelActiveMode() {
  addMenuOpen.value = false
  placingType.value = null
  linkingSourceId.value = null
  menuNodeId.value = null
}

function onShortcut(event: KeyboardEvent) {
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
  clearTimeout(centerAnimationTimer)
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
  cursor: url('/cursors/magnifier.svg') 11 11, zoom-in;
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
.board-world.centering { transition:transform 420ms cubic-bezier(.32,.72,0,1); }
.edge-layer { position:absolute; z-index:1; top:0; left:0; width:1px; height:1px; pointer-events:auto; overflow:visible; }
.board-card { position:absolute; z-index:2; top:0; left:0; cursor:grab; will-change:transform; }
.board-card:active { cursor:grabbing; }

.canvas-heading { position:absolute; z-index:12; top:24px; left:28px; pointer-events:none; }
.canvas-heading>* { pointer-events:auto; }

.placement-hint { position:absolute; z-index:20; left:50%; bottom:98px; transform:translateX(-50%); display:flex; align-items:center; gap:9px; padding:10px 12px 10px 15px; color:#f8f1e6; background:rgba(41,36,30,.94); border-radius:999px; box-shadow:0 14px 30px rgba(39,30,21,.3); font-size:12px; }
.placement-dot { width:7px; height:7px; border-radius:50%; background:#e9a67d; box-shadow:0 0 0 5px rgba(233,166,125,.12); }
.placement-hint button { border:0; color:#e8b69a; background:transparent; cursor:pointer; }
.placement-enter-active,.placement-leave-active { transition:opacity .18s ease-out,transform .2s cubic-bezier(.23,1,.32,1); }
.placement-enter-from,.placement-leave-to { opacity:0; transform:translate(-50%,10px); }

.add-note-dock { position:absolute; bottom:24px; left:28px; z-index:22; width:108px; height:50px; }
.add-note-trigger { position:absolute; z-index:3; inset:0; display:flex; align-items:center; gap:8px; box-sizing:border-box; padding:7px 9px 7px 18px; border:1px solid rgba(68,49,29,.34); border-radius:3px 5px 4px 3px; color:#49392a; background:repeating-linear-gradient(2deg,rgba(85,59,33,.026) 0 1px,transparent 1px 4px),linear-gradient(110deg,rgba(255,255,255,.38),transparent 55%),#dfcfad; box-shadow:4px 6px 13px rgba(52,36,20,.19),inset 0 1px rgba(255,255,255,.45); cursor:pointer; transform:rotate(-1.2deg); transform-origin:16px 42px; transition:transform 150ms cubic-bezier(.23,1,.32,1),box-shadow 150ms ease; }
.add-note-trigger::before { content:''; position:absolute; z-index:1; top:-1px; right:7px; left:7px; height:4px; border-top:1px solid rgba(68,49,29,.36); border-radius:50%; box-shadow:inset 0 2px 2px rgba(255,249,232,.42),0 -2px 3px rgba(54,37,20,.08); pointer-events:none; }
.card-stack { position:absolute; z-index:-1; inset:3px -3px -3px 3px; border:1px solid rgba(68,49,29,.2); border-radius:3px; background:#c7b58f; transform:rotate(3deg); }
.brass-fastener { position:absolute; top:8px; left:8px; width:7px; height:7px; border-radius:50%; background:radial-gradient(circle at 35% 30%,#f4d995 0 12%,#a9803d 48%,#5e431d 100%); box-shadow:0 1px 2px rgba(54,34,13,.35); }
.trigger-copy { min-width:0; display:flex; flex-direction:column; align-items:flex-start; gap:1px; }
.trigger-copy small { color:rgba(73,55,35,.5); font:6px var(--mono); letter-spacing:.15em; }
.trigger-copy strong { white-space:nowrap; font:600 12px/1.35 var(--serif); letter-spacing:.05em; }
.trigger-plus { margin-left:auto; color:#91483f; font:17px/1 var(--serif); transition:transform 180ms cubic-bezier(.23,1,.32,1); }
.add-note-dock.open .trigger-plus { transform:rotate(45deg); }
.add-note-trigger:focus-visible,.material-card:focus-visible { outline:2px solid rgba(145,72,63,.72); outline-offset:3px; }
.add-note-trigger:active { transform:rotate(-.7deg) scale(.97); }
.material-cards { position:absolute; z-index:2; inset:0; pointer-events:none; }
.material-card { position:absolute; bottom:5px; left:4px; width:100px; height:47px; box-sizing:border-box; padding:7px 8px 5px 12px; border:1px solid rgba(66,47,28,.28); border-radius:2px 4px 3px 2px; color:#49382a; background:repeating-linear-gradient(180deg,transparent 0 13px,rgba(87,108,111,.1) 13px 14px),linear-gradient(104deg,rgba(255,255,255,.3),transparent 56%),#ebdfc6; box-shadow:3px 5px 10px rgba(51,34,18,.14); text-align:left; cursor:pointer; opacity:1; pointer-events:none; transform:translate3d(5px,5px,0) rotate(-1deg) scale(.98); transform-origin:52px 45px; transition:transform 150ms cubic-bezier(.23,1,.32,1),box-shadow 130ms ease; }
.material-card::before { content:''; position:absolute; top:0; right:0; bottom:0; width:4px; background:rgba(143,65,56,.6); }
.material-code { position:absolute; top:6px; right:8px; color:rgba(75,57,37,.42); font:6px var(--mono); letter-spacing:.08em; }
.material-card strong,.material-card small { display:block; }
.material-card strong { font:600 13px/1.25 var(--serif); letter-spacing:.06em; }
.material-card small { margin-top:2px; color:rgba(72,55,37,.56); font:7px var(--mono); letter-spacing:.08em; }
.suspect-card { background:repeating-linear-gradient(180deg,transparent 0 13px,rgba(113,81,77,.09) 13px 14px),linear-gradient(104deg,rgba(255,255,255,.26),transparent 56%),#dcc3b7; }
.suspect-card::before { background:rgba(91,64,49,.48); }
.add-note-dock.open .material-card { pointer-events:auto; transition-duration:210ms,150ms; }
.add-note-dock.open .clue-card { transform:translate3d(-12px,-52px,0) rotate(-4deg) scale(1); }
.add-note-dock.open .suspect-card { transform:translate3d(75px,-50px,0) rotate(3deg) scale(1); transition-delay:32ms,0ms; }
@media (hover:hover) and (pointer:fine) {
  .add-note-trigger:hover { transform:rotate(-.5deg) translateY(-2px); box-shadow:5px 8px 16px rgba(52,36,20,.22),inset 0 1px rgba(255,255,255,.48); }
  .material-card:hover { z-index:4; box-shadow:5px 8px 15px rgba(51,34,18,.2); }
  .add-note-dock.open .clue-card:hover { transform:translate3d(-12px,-55px,0) rotate(-2.5deg) scale(1.03); }
  .add-note-dock.open .suspect-card:hover { transform:translate3d(75px,-53px,0) rotate(1.5deg) scale(1.03); }
}

.center-btn { width:36px; height:36px; border-radius:50%; border:1px solid rgba(79,61,42,.21); background:rgba(245,237,219,.91); display:flex; align-items:center; justify-content:center; cursor:pointer; box-shadow:0 3px 9px rgba(57,44,28,.13); transition:transform 190ms cubic-bezier(.23,1,.32,1),background-color 160ms ease,opacity 190ms ease; line-height:0; padding:0; }
.center-btn:hover { background:var(--white); transform:scale(1.06); }
.center-btn:active { transform:scale(.96); }
.center-btn svg { width:18px; height:18px; fill:none; stroke:var(--ink-soft); stroke-width:1.7; }
.canvas-area.panel-open .center-btn { opacity:0; pointer-events:none; transform:scale(.94); }

.edge-edit-toolbar { position:fixed; transform:translate(-50%,-50%); z-index:1000; display:flex; gap:10px; align-items:center; }
.edge-edit-input-wrapper { background:rgba(255,253,248,.96); border-radius:24px; box-shadow:0 2px 8px rgba(0,0,0,.1); border:1px solid var(--rust); padding:4px 12px; }
.edge-edit-input-wrapper input { border:0; background:transparent; outline:0; font-size:16px; padding:6px 0; min-width:120px; text-align:center; color:var(--text); }
.edge-delete-btn { background:white; border:1px solid #ddd; border-radius:50%; width:34px; height:34px; cursor:pointer; display:flex; align-items:center; justify-content:center; box-shadow:0 2px 6px rgba(0,0,0,.1); padding:0; }
.edge-delete-btn:hover { background:#ffebee; border-color:#c62828; color:#c62828; }

@media (max-width:760px) {
  .canvas-heading { left:14px; }
  .add-note-dock { left:14px; bottom:14px; }
}

@media (prefers-reduced-motion:reduce) {
  .board-world,.board-card { will-change:auto; }
  .board-world.centering,.center-btn { transition-duration:.01ms; }
  .add-note-trigger,.material-card,.trigger-plus { transition-duration:.01ms; }
}
</style>
