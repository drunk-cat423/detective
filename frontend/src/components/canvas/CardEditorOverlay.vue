<template>
  <article
    class="card-editor-card"
    :data-card="node.data.cardStyle || (node.data.type === 'suspect' ? 'dossier' : 'memo')"
    :style="editorStyle"
    role="dialog"
    aria-modal="true"
    aria-labelledby="card-editor-title"
    @click.stop
    @pointerdown.stop
  >
    <span class="editor-paper-shadow" aria-hidden="true"></span>
    <span class="editor-pin-stem" aria-hidden="true"></span>
    <span class="editor-pin-head" aria-hidden="true"></span>

    <div class="editor-paper">
      <button class="editor-close" type="button" aria-label="关闭编辑卡片" @click="emit('close')">×</button>

      <header class="editor-heading">
        <span>{{ kicker }}</span>
        <h2 id="card-editor-title">{{ node.data.type === 'suspect' ? '人物档案' : '线索记录' }}</h2>
        <small>#{{ String(node.id).padStart(3, '0') }}</small>
      </header>

      <label v-if="node.data.type === 'suspect'" class="editor-field editor-name">
        <span>姓名</span>
        <input ref="nameInput" v-model="draftName" placeholder="未知人物" maxlength="80" />
      </label>

      <label class="editor-field editor-content">
        <span>{{ node.data.type === 'suspect' ? '人物记录' : '线索内容' }}</span>
        <textarea
          ref="contentInput"
          v-model="draftContent"
          :placeholder="node.data.type === 'suspect' ? '记录人物身份、行为和疑点…' : '在纸上写下线索…'"
          maxlength="4000"
        ></textarea>
      </label>

      <div class="paper-choices" aria-label="选择纸张颜色">
        <span>纸张</span>
        <button
          v-for="color in presetColors"
          :key="color"
          type="button"
          :class="{ active: draftColor === color }"
          :style="{ '--swatch': color }"
          :aria-label="`选择纸张颜色 ${color}`"
          :aria-pressed="draftColor === color"
          @click="draftColor = color"
        ></button>
      </div>

      <footer class="editor-actions">
        <button class="delete-action" :class="{ armed: deleteArmed }" type="button" @click="requestDelete">
          {{ deleteArmed ? '再次点击确认作废' : '作废此卡' }}
        </button>
        <span class="editor-spacer"></span>
        <button class="cancel-action" type="button" @click="emit('close')">放回原处</button>
        <button class="save-action" type="button" @click="save"><span>保存记录</span><i aria-hidden="true">✓</i></button>
      </footer>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, type CSSProperties } from 'vue'

const props = defineProps<{
  node: any
  presetColors: string[]
}>()

const emit = defineEmits<{
  save: [payload: { content: string; name: string; color: string }]
  close: []
  delete: []
}>()

const draftContent = ref(props.node?.data?.content ?? '')
const draftName = ref(props.node?.data?.name ?? '')
const draftColor = ref(props.node?.data?.color ?? '#F4EDDC')
const deleteArmed = ref(false)
const nameInput = ref<HTMLInputElement | null>(null)
const contentInput = ref<HTMLTextAreaElement | null>(null)
let deleteTimer: number | undefined

const kicker = computed(() => props.node.data.type === 'suspect'
  ? 'PERSON FILE / 人物档案'
  : 'EVIDENCE RECORD / 线索记录')
const editorStyle = computed<CSSProperties>(() => ({ '--editor-paper': draftColor.value }))

function save() {
  emit('save', {
    content: draftContent.value.trim(),
    name: draftName.value.trim(),
    color: draftColor.value,
  })
}

function requestDelete() {
  if (deleteArmed.value) {
    window.clearTimeout(deleteTimer)
    emit('delete')
    return
  }
  deleteArmed.value = true
  deleteTimer = window.setTimeout(() => { deleteArmed.value = false }, 2400)
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    event.preventDefault()
    emit('close')
  }
  if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
    event.preventDefault()
    save()
  }
}

onMounted(async () => {
  window.addEventListener('keydown', onKeydown)
  await nextTick()
  ;(props.node.data.type === 'suspect' ? nameInput.value : contentInput.value)?.focus()
})

onBeforeUnmount(() => {
  window.clearTimeout(deleteTimer)
  window.removeEventListener('keydown', onKeydown)
})
</script>

<style scoped>
.card-editor-card {
  --editor-paper: #f4eddc;
  position: relative;
  width: min(540px, calc(100vw - 44px));
  height: min(570px, calc(100vh - 92px));
  min-height: 430px;
  color: #30291f;
  transform: rotate(-.45deg);
  transform-origin: center;
  cursor: url('/cursors/pencil.svg') 3 25, text;
}

.editor-paper-shadow,
.editor-paper {
  position: absolute;
  inset: 0;
  border-radius: 3px;
}
.editor-paper-shadow { background: rgba(42, 28, 16, .42); filter: blur(14px); transform: translate(13px, 19px) rotate(.8deg); }
.editor-paper {
  z-index: 2;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  padding: 48px 46px 30px 58px;
  overflow: hidden;
  border: 1px solid rgba(79, 55, 31, .16);
  background:
    repeating-linear-gradient(180deg, transparent 0 31px, rgba(87, 118, 135, .13) 31px 32px),
    linear-gradient(90deg, transparent 0 35px, rgba(158, 67, 60, .27) 35px 37px, transparent 37px),
    linear-gradient(104deg, rgba(255,255,255,.52), transparent 42%),
    color-mix(in srgb, var(--editor-paper) 84%, #f5e8c8);
  box-shadow: inset 0 0 24px rgba(87, 58, 29, .08);
}
.card-editor-card[data-card="ticket"] .editor-paper { clip-path: polygon(0 0,100% 0,100% 36%,98% 39%,97% 50%,98% 61%,100% 64%,100% 100%,0 100%,0 64%,2% 61%,3% 50%,2% 39%,0 36%); }
.card-editor-card[data-card="torn"] .editor-paper { clip-path: polygon(1% 1%,9% 0,18% 1%,27% 0,39% 1%,50% 0,62% 1%,74% 0,86% 1%,99% 0,100% 96%,92% 99%,83% 97%,73% 100%,63% 98%,52% 100%,41% 98%,30% 100%,19% 98%,8% 100%,0 97%); }
.card-editor-card[data-card="dossier"] .editor-paper { background: linear-gradient(90deg, rgba(146,62,51,.7) 0 8px, transparent 8px), repeating-linear-gradient(180deg, transparent 0 31px, rgba(87,118,135,.1) 31px 32px), linear-gradient(104deg,rgba(255,255,255,.5),transparent 42%), color-mix(in srgb,var(--editor-paper) 85%,#f0d8c9); }

.editor-pin-stem,.editor-pin-head { position: absolute; z-index: 8; left: 32%; pointer-events: none; transform: translateX(-50%); }
.editor-pin-stem { top: -5px; width: 4px; height: 26px; background: linear-gradient(90deg,#55504b,#ddd5ca 55%,#4d4844); box-shadow: 2px 3px 3px rgba(25,16,10,.3); }
.editor-pin-head { top: -18px; width: 31px; height: 25px; border-radius: 50% 50% 45% 45%; background: radial-gradient(circle at 34% 25%,#ffe1cd 0 8%,#b34b3f 25%,#762a27 68%,#351515 100%); box-shadow: 0 6px 9px rgba(35,18,12,.42),inset -3px -3px 5px rgba(52,14,13,.32); }

.editor-close { position: absolute; z-index: 5; top: 18px; right: 19px; width: 31px; height: 31px; padding: 0; border: 1px solid rgba(77,57,37,.18); border-radius: 50%; color: rgba(65,52,38,.65); background: rgba(244,237,220,.58); cursor: pointer; font: 22px/1 var(--serif); transition: transform 140ms cubic-bezier(.23,1,.32,1),background-color 140ms ease; }
.editor-close:active { transform: scale(.95); }
.editor-heading { position: relative; padding-bottom: 18px; border-bottom: 1px solid rgba(75,61,43,.24); }
.editor-heading::after { content:''; position:absolute; left:0; bottom:-2px; width:86px; border-bottom:3px solid #98493f; transform:rotate(-1deg); }
.editor-heading span { color: rgba(68,56,41,.56); font: 8px var(--mono); letter-spacing: .18em; }
.editor-heading h2 { margin: 3px 0 0; font: 600 31px/1.2 var(--serif); letter-spacing: .055em; }
.editor-heading small { position: absolute; right: 0; bottom: 20px; color: rgba(70,57,41,.42); font: 9px var(--mono); letter-spacing: .12em; }

.editor-field { display:flex; flex-direction:column; gap:7px; margin-top:18px; }
.editor-field>span,.paper-choices>span { color: rgba(68,54,39,.66); font: 9px var(--mono); letter-spacing: .15em; }
.editor-field input,.editor-field textarea { box-sizing:border-box; width:100%; border:0; outline:0; color:#342c22; background:rgba(255,252,242,.24); font-family:"KaiTi","STKaiti","FangSong",var(--serif); cursor:url('/cursors/pencil.svg') 3 25,text; box-shadow:inset 0 -1px rgba(77,62,42,.18); transition:background-color 140ms ease,box-shadow 140ms ease; }
.editor-field input:focus,.editor-field textarea:focus { background:rgba(255,253,246,.48); box-shadow:inset 0 -2px rgba(147,68,59,.45); }
.editor-name input { height:43px; padding:6px 9px; font-size:23px; }
.editor-content { flex:1; min-height:0; }
.editor-content textarea { flex:1; min-height:150px; resize:none; padding:10px 9px; font-size:20px; line-height:1.58; }

.paper-choices { display:flex; align-items:center; gap:9px; min-height:34px; margin-top:12px; }
.paper-choices>span { margin-right:4px; }
.paper-choices button { --swatch:#f4eddc; width:24px; height:24px; padding:0; border:2px solid rgba(255,255,255,.75); border-radius:50%; background:var(--swatch); box-shadow:0 0 0 1px rgba(74,56,35,.15),0 2px 4px rgba(52,37,21,.1); cursor:pointer; transition:transform 140ms cubic-bezier(.23,1,.32,1),box-shadow 140ms ease; }
.paper-choices button.active { transform:scale(1.16); box-shadow:0 0 0 2px rgba(148,68,59,.46),0 3px 6px rgba(52,37,21,.14); }

.editor-actions { position:relative; display:flex; align-items:center; gap:13px; min-height:48px; margin-top:13px; padding-top:17px; }
.editor-actions::before { content:''; position:absolute; top:0; right:0; left:0; border-top:1px solid rgba(75,61,43,.2); transform:rotate(-.25deg); }
.editor-actions button { cursor:pointer; transition:transform 140ms cubic-bezier(.23,1,.32,1),background-color 140ms ease,color 140ms ease,border-color 140ms ease; }
.delete-action { min-height:32px; padding:4px 9px; border:2px solid rgba(143,55,49,.58); border-radius:1px; color:rgba(137,51,46,.72); background:rgba(255,250,240,.08); font:600 12px var(--serif); letter-spacing:.09em; opacity:.78; transform:rotate(-3deg); mix-blend-mode:multiply; }
.delete-action:active { transform:rotate(-3deg) scale(.96); }
.delete-action.armed { border-color:#89332e; color:#7e2d29; background:rgba(154,65,58,.12); opacity:1; transform:rotate(-1deg); }
.editor-spacer { flex:1; }
.cancel-action { min-height:31px; padding:4px 2px; border:0; border-bottom:1px solid rgba(73,58,41,.42); border-radius:0; color:rgba(73,58,41,.72); background:transparent; font:12px var(--serif); letter-spacing:.05em; transform:rotate(.7deg); }
.cancel-action:active { transform:rotate(.7deg) scale(.96); }
.save-action { min-width:112px; min-height:38px; display:flex; align-items:center; justify-content:center; gap:9px; padding:0 15px 0 17px; overflow:hidden; border:0; border-radius:0; color:#7f3b35; background:repeating-linear-gradient(2deg,rgba(99,73,48,.035) 0 1px,transparent 1px 4px),#e6d7b9; box-shadow:0 5px 11px rgba(62,43,23,.16),inset 0 1px rgba(255,255,255,.48); clip-path:polygon(2% 8%,96% 0,100% 82%,93% 100%,4% 93%,0 20%); font:600 13px var(--serif); letter-spacing:.08em; transform:rotate(-1deg); }
.save-action span { position:relative; z-index:1; }
.save-action i { color:#98483f; font:700 15px/1 var(--sans); font-style:normal; }
.save-action:active { transform:rotate(-1deg) scale(.96); }

@media (hover:hover) and (pointer:fine) {
  .editor-close:hover { background:rgba(255,253,247,.8); transform:scale(1.04); }
  .paper-choices button:hover { transform:scale(1.1); }
  .delete-action:hover { opacity:1; transform:rotate(-2deg) scale(1.025); }
  .cancel-action:hover { color:#332a20; border-bottom-color:#8b463f; transform:rotate(0); }
  .save-action:hover { color:#6f302b; transform:rotate(-.4deg) translateY(-2px); box-shadow:0 8px 15px rgba(62,43,23,.19),inset 0 1px rgba(255,255,255,.5); }
}
@media (max-width:620px) {
  .card-editor-card { height:min(620px,calc(100vh - 48px)); }
  .editor-paper { padding:43px 25px 22px 38px; }
  .editor-heading h2 { font-size:26px; }
  .editor-content textarea { font-size:17px; }
  .paper-choices { gap:7px; }
  .paper-choices button { width:22px;height:22px; }
}
</style>
