<template>
  <div
    class="note-node"
    :class="{
      'is-dimmed': isDimmed,
      'is-match': isMatch,
      'is-selected-card': isSelected,
      'is-link-source': isLinkSource,
      'has-thread': hasThread,
    }"
    :style="nodeStyle"
    :data-type="data.type"
    :data-card="cardStyle"
  >
    <span class="pin-stem" aria-hidden="true"></span>
    <span class="pin-collar" aria-hidden="true"></span>
    <span class="pin-head" aria-hidden="true"></span>
    <button class="pin-hit" type="button" title="从这里牵线" aria-label="从这张卡片的图钉牵线" @pointerdown.stop @click.stop="startLink"></button>

    <div class="paper-shadow" aria-hidden="true"></div>
    <div class="paper-surface">
      <span class="paper-margin" aria-hidden="true"></span>
      <span class="paper-perforation" aria-hidden="true"></span>
      <span class="paper-stamp" aria-hidden="true">FILED</span>
      <span class="paper-kicker">{{ kickerLabel }}</span>
      <div class="paper-writing">
        <strong v-if="data.type === 'suspect' && data.name" class="person-name">{{ data.name }}</strong>
        <p class="paper-copy">{{ data.content }}</p>
      </div>
      <span class="paper-index">{{ indexLabel }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, inject, type CSSProperties, type Ref } from 'vue'
import { nodeSeed, pinPercent } from '@/utils/boardGeometry'

const props = defineProps<{
  id: string
  data: { content: string; type: string; color: string; name?: string; cardStyle?: string }
}>()

const searchQuery = inject<Ref<string>>('noteSearchQuery')
const selectedNodeId = inject<Ref<string | undefined>>('selectedNodeId')
const linkingSourceId = inject<Ref<string | null>>('linkingSourceId')
const linkedPins = inject<Ref<Set<string>>>('linkedPins')
const runNodeAction = inject<(action: 'link', nodeId: string) => void>('runNodeAction')

const numericSeed = computed(() => nodeSeed(props.id))
const clueCardStyles = ['torn', 'memo', 'index', 'ticket', 'clipping'] as const
const cardStyle = computed(() => props.data.cardStyle
  || (props.data.type === 'suspect' ? 'dossier' : clueCardStyles[numericSeed.value % clueCardStyles.length]))
const kickerLabel = computed(() => ({
  torn: 'EVIDENCE NOTE / 线索',
  memo: 'FIELD MEMO / 现场备忘',
  index: 'INDEX CARD / 索引卡',
  ticket: 'EVIDENCE SLIP / 线索票据',
  clipping: 'CASE EXCERPT / 案件摘录',
  dossier: 'PERSON FILE / 人物档案',
}[cardStyle.value] || 'EVIDENCE / 线索'))
const pinX = computed(() => pinPercent(props.id))
const rotation = computed(() => ((numericSeed.value % 9) - 4) * 0.32)
const nodeStyle = computed<CSSProperties>(() => ({
  '--paper-color': props.data.color,
  '--pin-x': `${pinX.value}%`,
  '--paper-rotation': `${rotation.value}deg`,
}))
const indexLabel = computed(() => `#${String(props.id).padStart(3, '0')}`)
const normalizedQuery = computed(() => searchQuery?.value.trim().toLowerCase() ?? '')
const isMatch = computed(() => {
  if (!normalizedQuery.value) return false
  return [props.data.content, props.data.name, props.data.type]
    .filter(Boolean)
    .some(value => String(value).toLowerCase().includes(normalizedQuery.value))
})
const isSelected = computed(() => selectedNodeId?.value === props.id)
const isLinkSource = computed(() => linkingSourceId?.value === props.id)
const hasThread = computed(() => linkedPins?.value.has(String(props.id)) ?? false)
const isDimmed = computed(() => {
  if (normalizedQuery.value) return !isMatch.value
  const focusId = linkingSourceId?.value || selectedNodeId?.value
  return Boolean(focusId && focusId !== props.id)
})

function startLink() {
  runNodeAction?.('link', props.id)
}
</script>

<style scoped>
.note-node {
  width: 100%;
  height: 100%;
  min-width: 168px;
  min-height: 112px;
  position: relative;
  cursor: grab;
  transform-origin: var(--pin-x) 0;
  transition: opacity .22s ease, filter .22s ease;
}

.note-node:active { cursor: grabbing; }

.paper-shadow,
.paper-surface {
  position: absolute;
  inset: 0;
  transform: rotate(var(--paper-rotation));
  transform-origin: var(--pin-x) 0;
  transition: transform .28s cubic-bezier(.22,1,.36,1), filter .28s ease;
}

.note-node[data-card="torn"] .paper-shadow,
.note-node[data-card="torn"] .paper-surface {
  clip-path: polygon(1% 3%, 10% 1%, 20% 3%, 31% 1%, 42% 2%, 53% 0, 64% 2%, 76% 1%, 88% 3%, 99% 1%, 100% 89%, 97% 96%, 89% 94%, 81% 99%, 72% 96%, 63% 99%, 54% 96%, 45% 99%, 35% 96%, 25% 99%, 15% 96%, 5% 99%, 0 94%);
}

.note-node[data-card="memo"] .paper-shadow,
.note-node[data-card="memo"] .paper-surface {
  clip-path: polygon(1% 1%, 98% 0, 100% 96%, 95% 99%, 88% 97%, 80% 100%, 72% 98%, 64% 100%, 56% 98%, 48% 100%, 40% 98%, 32% 100%, 24% 98%, 16% 100%, 8% 97%, 1% 99%);
}

.note-node[data-card="index"] .paper-shadow,
.note-node[data-card="index"] .paper-surface {
  clip-path: polygon(1% 1%, 99% 0, 100% 98%, 1% 100%, 0 3%);
}

.note-node[data-card="ticket"] .paper-shadow,
.note-node[data-card="ticket"] .paper-surface {
  clip-path: polygon(0 0, 100% 0, 100% 35%, 96% 38%, 94% 50%, 96% 62%, 100% 65%, 100% 100%, 0 100%, 0 66%, 4% 62%, 6% 50%, 4% 38%, 0 34%);
}

.note-node[data-card="clipping"] .paper-shadow,
.note-node[data-card="clipping"] .paper-surface {
  clip-path: polygon(1% 1%, 98% 0, 100% 7%, 98% 14%, 100% 23%, 98% 32%, 100% 42%, 98% 51%, 100% 61%, 98% 72%, 100% 83%, 98% 98%, 88% 96%, 76% 99%, 64% 97%, 52% 100%, 40% 97%, 28% 99%, 16% 96%, 1% 99%, 2% 83%, 0 65%, 2% 47%, 0 28%, 2% 13%);
}

.note-node[data-card="dossier"] .paper-shadow,
.note-node[data-card="dossier"] .paper-surface {
  clip-path: polygon(0 3%, 7% 1%, 36% 2%, 40% 0, 64% 0, 68% 2%, 99% 1%, 100% 97%, 96% 100%, 3% 98%);
}

.paper-shadow {
  z-index: 0;
  background: rgba(37, 22, 11, .42);
  filter: blur(5px);
  transform: translate(7px, 10px) rotate(var(--paper-rotation));
}

.paper-surface {
  z-index: 2;
  display: flex;
  flex-direction: column;
  padding: 19px 17px 14px;
  overflow: hidden;
  color: #30291f;
  background:
    linear-gradient(104deg, rgba(255,255,255,.46), transparent 38%),
    linear-gradient(176deg, transparent 68%, rgba(91,64,33,.08)),
    color-mix(in srgb, var(--paper-color, #f1e8d4) 88%, #fff4d8);
  border: 1px solid rgba(77, 51, 26, .08);
}

.note-node[data-card="memo"] .paper-surface {
  padding: 22px 17px 13px 25px;
  background:
    repeating-linear-gradient(180deg, transparent 0 25px, rgba(91,126,145,.22) 25px 26px),
    linear-gradient(103deg, rgba(255,255,255,.52), transparent 44%),
    color-mix(in srgb, var(--paper-color, #efe8d3) 78%, #f7edc9);
}

.note-node[data-card="index"] .paper-surface {
  padding: 19px 18px 11px 25px;
  background:
    repeating-linear-gradient(180deg, transparent 0 23px, rgba(82,119,143,.24) 23px 24px),
    linear-gradient(90deg, transparent 0 17px, rgba(176,77,67,.34) 17px 18px, transparent 18px),
    #eee4c8;
}

.note-node[data-card="ticket"] .paper-surface {
  padding: 17px 28px 13px 18px;
  background:
    radial-gradient(circle at 84% 50%, rgba(92,63,34,.11) 0 1px, transparent 1.5px) 0 0 / 6px 6px,
    linear-gradient(102deg, rgba(255,255,255,.38), transparent 48%),
    color-mix(in srgb, var(--paper-color, #ead7af) 72%, #e3c58c);
}

.note-node[data-card="clipping"] .paper-surface {
  padding: 18px 15px 13px;
  background:
    repeating-linear-gradient(0deg, rgba(66,57,45,.025) 0 1px, transparent 1px 3px),
    linear-gradient(107deg, rgba(255,255,255,.34), transparent 45%),
    #e8e1d2;
}

.note-node[data-card="dossier"] .paper-surface {
  padding: 24px 18px 14px;
  background:
    linear-gradient(90deg, rgba(146,62,51,.65) 0 5px, transparent 5px),
    linear-gradient(105deg, rgba(255,255,255,.36), transparent 46%),
    color-mix(in srgb, var(--paper-color, #e7c7bf) 82%, #efd9c8);
}

.paper-margin,
.paper-perforation,
.paper-stamp { display: none; position: absolute; pointer-events: none; }

.note-node[data-card="memo"] .paper-margin,
.note-node[data-card="index"] .paper-margin {
  display: block;
  z-index: 1;
  top: 0;
  bottom: 0;
  left: 17px;
  width: 1px;
  background: rgba(174,71,65,.38);
}

.note-node[data-card="ticket"] .paper-perforation {
  display: block;
  z-index: 1;
  top: 9px;
  bottom: 9px;
  right: 25px;
  border-left: 1px dashed rgba(81,59,34,.38);
}

.note-node[data-card="dossier"] .paper-stamp {
  display: block;
  z-index: 1;
  right: 11px;
  bottom: 13px;
  padding: 2px 5px;
  border: 1px solid rgba(132,47,42,.42);
  color: rgba(132,47,42,.52);
  font: 7px var(--mono);
  letter-spacing: .12em;
  transform: rotate(-7deg);
}

.paper-surface::before,
.paper-surface::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.paper-surface::before {
  opacity: .28;
  background-image:
    repeating-linear-gradient(8deg, transparent 0 5px, rgba(91,62,29,.035) 5px 6px),
    radial-gradient(ellipse at center, rgba(75,48,22,.26) 0 .45px, transparent .6px);
  background-size: auto, 5px 4px;
  mix-blend-mode: multiply;
}

.paper-surface::after { box-shadow: inset 0 0 13px rgba(96,67,33,.06); }

.paper-kicker,
.paper-index {
  position: relative;
  z-index: 1;
  font-family: var(--mono);
  color: rgba(67,54,39,.56);
  font-size: 7px;
  letter-spacing: .16em;
}

.paper-writing {
  position: relative;
  z-index: 1;
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 0;
  padding: 6px 1px 3px;
}

.person-name {
  margin-bottom: 4px;
  color: #2c251c;
  font-family: "KaiTi", "STKaiti", "FangSong", var(--serif);
  font-size: 18px;
  font-weight: 700;
}

.paper-copy {
  display: -webkit-box;
  margin: 0;
  overflow: hidden;
  color: #40372b;
  font-family: "KaiTi", "STKaiti", "FangSong", var(--serif);
  font-size: 15px;
  line-height: 1.38;
  letter-spacing: .025em;
  white-space: pre-wrap;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

.note-node[data-card="memo"] .paper-copy,
.note-node[data-card="index"] .paper-copy { line-height: 1.52; }

.note-node[data-card="ticket"] .paper-copy { font-size: 14px; -webkit-line-clamp: 2; }

.note-node[data-card="clipping"] .paper-copy {
  font-family: "FangSong", "STFangsong", var(--serif);
  font-size: 13px;
  line-height: 1.46;
  text-align: justify;
  -webkit-line-clamp: 5;
}

.note-node[data-card="clipping"] .paper-kicker {
  padding-bottom: 5px;
  border-bottom: 1px solid rgba(70,59,44,.32);
  font-family: var(--serif);
  font-size: 8px;
  font-weight: 700;
}

.note-node[data-card="ticket"] .paper-index { margin-right: 14px; }

.paper-index { align-self: flex-end; letter-spacing: .08em; }

.pin-stem,
.pin-collar,
.pin-head {
  position: absolute;
  left: var(--pin-x);
  z-index: 12;
  pointer-events: none;
  transform: translateX(-50%);
}

.pin-hit {
  position: absolute;
  z-index: 14;
  top: -17px;
  left: var(--pin-x);
  width: 34px;
  height: 34px;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: transparent;
  cursor: crosshair;
  transform: translateX(-50%);
}
.pin-hit:focus-visible { outline: 2px solid rgba(143, 54, 46, .7); outline-offset: 2px; }
.pin-hit:hover ~ .paper-shadow { filter: blur(7px); }

.pin-stem {
  top: -1px;
  width: 2px;
  height: 11px;
  background: linear-gradient(90deg, #65605a, #ddd6ca 55%, #58534e);
  box-shadow: 1px 2px 2px rgba(24,16,10,.28);
}

.pin-collar {
  top: -4px;
  width: 12px;
  height: 8px;
  border-radius: 50%;
  background: radial-gradient(ellipse at 40% 32%, #e5ded2 0 10%, #918b82 38%, #4f4b46 70%);
  box-shadow: 0 2px 3px rgba(31,20,12,.42);
}

.pin-head {
  top: -10px;
  width: 15px;
  height: 12px;
  border-radius: 50% 50% 45% 45%;
  background: radial-gradient(circle at 34% 26%, #ffddc4 0 8%, #b34b3f 25%, #7e2d29 68%, #3e1918 100%);
  box-shadow: 0 3px 5px rgba(34,18,13,.45), inset -2px -2px 3px rgba(56,16,14,.35);
}

.note-node:hover .paper-surface,
.note-node.is-match .paper-surface,
.note-node.is-selected-card .paper-surface,
.note-node.is-link-source .paper-surface {
  transform: translateY(-4px) rotate(calc(var(--paper-rotation) * .35)) scale(1.025);
  filter: brightness(1.025);
}

.note-node:hover .paper-shadow,
.note-node.is-link-source .paper-shadow {
  transform: translate(9px, 14px) rotate(calc(var(--paper-rotation) * .35)) scale(1.025);
  filter: blur(7px);
}

.note-node.is-link-source .pin-head { animation: pinPulse 1.05s ease-in-out infinite; }
.note-node.is-dimmed { opacity: .24; filter: grayscale(.6); }

@keyframes pinPulse {
  50% { box-shadow: 0 3px 5px rgba(34,18,13,.45), 0 0 0 8px rgba(177,67,55,.18), inset -2px -2px 3px rgba(56,16,14,.35); }
}

@media (prefers-reduced-motion: reduce) {
  .note-node.is-link-source .pin-head { animation: none; }
}
</style>
